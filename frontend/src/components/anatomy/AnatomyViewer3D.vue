<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import {
  ANATOMY_SYSTEMS_3D,
  ATLAS_3D_URL,
  system3DColor,
  system3DName,
  type Atlas3D,
  type AtlasPart
} from '../../data/anatomy3d';

const props = withDefaults(defineProps<{
  hiddenSystems?: string[];
  focusSystems?: string[];
  selectedId?: string;
  autoRotate?: boolean;
}>(), {
  hiddenSystems: () => [],
  focusSystems: () => [],
  selectedId: '',
  autoRotate: false
});

const emit = defineEmits<{
  (event: 'select', payload: { id: string; name: string; system: string; systemName: string }): void;
  (event: 'clear'): void;
  (event: 'ready', payload: { parts: number; triangles: number; systems: Record<string, number> }): void;
  (event: 'error', message: string): void;
}>();

const host = ref<HTMLDivElement | null>(null);
const loading = ref(true);
const progress = ref(0);
const note = ref('正在载入三维解剖模型');
const failed = ref('');
const layers = shallowRef<SystemLayer[]>([]);

const HIGHLIGHT = new THREE.Color('#f2a33b');

// Painter order: deep structures first, surface vessels last.
const DRAW_ORDER = [
  'skeletal', 'nervous', 'digestive', 'respiratory', 'urinary',
  'reproductive', 'endocrine', 'lymphatic', 'cardiac', 'arterial', 'venous'
];

interface PartRange {
  id: string;
  name: string;
  system: string;
  vertexStart: number;
  vertexCount: number;
  faceStart: number;
  faceCount: number;
}

interface SystemLayer {
  id: string;
  mesh: THREE.Mesh;
  geometry: THREE.BufferGeometry;
  material: THREE.MeshStandardMaterial;
  colorAttribute: THREE.BufferAttribute;
  ranges: PartRange[];
  faceStarts: number[];
}

const scene = shallowRef<THREE.Scene | null>(null);
const camera = shallowRef<THREE.PerspectiveCamera | null>(null);
const renderer = shallowRef<THREE.WebGLRenderer | null>(null);
const controls = shallowRef<OrbitControls | null>(null);

let manifest: Atlas3D | null = null;
let partsBySystem = new Map<string, AtlasPart[]>();
let chunkIndexBySystem = new Map<string, number>();
const loadedSystems = new Set<string>();
const systemBoundsMap = new Map<string, THREE.Box3>();
let overallBounds = new THREE.Box3();
let cameraTween: {
  fromPosition: THREE.Vector3;
  toPosition: THREE.Vector3;
  fromTarget: THREE.Vector3;
  toTarget: THREE.Vector3;
  startedAt: number;
} | null = null;

let frameHandle = 0;
let dirty = true;
let observer: ResizeObserver | null = null;
let pointerDown: { x: number; y: number } | null = null;
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

function markDirty() {
  dirty = true;
}

function buildLayer(systemId: string, parts: AtlasPart[], buffer: ArrayBuffer): SystemLayer {
  const vertexTotal = parts.reduce((total, part) => total + part.vertexCount, 0);
  const indexTotal = parts.reduce((total, part) => total + part.indexCount, 0);

  const positions = new Float32Array(vertexTotal * 3);
  const normals = new Int16Array(vertexTotal * 3);
  const colors = new Float32Array(vertexTotal * 3);
  const indices = new Uint32Array(indexTotal);

  const ranges: PartRange[] = [];
  const bounds = new THREE.Box3();
  let vertexOffset = 0;
  let indexOffset = 0;

  for (const part of parts) {
    const partPositions = new Float32Array(buffer, part.positions, part.vertexCount * 3);
    const partNormals = new Int16Array(buffer, part.normals, part.vertexCount * 3);
    const partIndices = new Uint32Array(buffer, part.indices, part.indexCount);

    positions.set(partPositions, vertexOffset * 3);
    normals.set(partNormals, vertexOffset * 3);
    for (let index = 0; index < part.indexCount; index += 1) {
      indices[indexOffset + index] = partIndices[index] + vertexOffset;
    }

    bounds.expandByPoint(new THREE.Vector3().fromArray(part.bounds[0]));
    bounds.expandByPoint(new THREE.Vector3().fromArray(part.bounds[1]));

    ranges.push({
      id: part.id,
      name: part.name,
      system: systemId,
      vertexStart: vertexOffset,
      vertexCount: part.vertexCount,
      faceStart: indexOffset / 3,
      faceCount: part.indexCount / 3
    });

    vertexOffset += part.vertexCount;
    indexOffset += part.indexCount;
  }

  systemBoundsMap.set(systemId, bounds);

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  // Normals arrive as signed 16-bit values that the GPU normalises on read.
  geometry.setAttribute('normal', new THREE.BufferAttribute(normals, 3, true));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  geometry.setIndex(new THREE.BufferAttribute(indices, 1));
  geometry.computeBoundingSphere();

  const material = new THREE.MeshStandardMaterial({
    vertexColors: true,
    roughness: 0.74,
    metalness: 0.04
  });

  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = `system-${systemId}`;
  mesh.userData.system = systemId;
  mesh.renderOrder = Math.max(DRAW_ORDER.indexOf(systemId), 0);

  const layer: SystemLayer = {
    id: systemId,
    mesh,
    geometry,
    material,
    colorAttribute: geometry.getAttribute('color') as THREE.BufferAttribute,
    ranges,
    faceStarts: ranges.map((range) => range.faceStart)
  };

  paintLayer(layer, props.selectedId);
  return layer;
}

function paintLayer(layer: SystemLayer, selectedId: string) {
  const base = new THREE.Color(system3DColor(layer.id));
  const colors = layer.colorAttribute.array as Float32Array;

  for (const range of layer.ranges) {
    const color = range.id === selectedId ? HIGHLIGHT : base;
    for (let index = 0; index < range.vertexCount; index += 1) {
      const offset = (range.vertexStart + index) * 3;
      colors[offset] = color.r;
      colors[offset + 1] = color.g;
      colors[offset + 2] = color.b;
    }
  }

  layer.colorAttribute.needsUpdate = true;
  markDirty();
}

function repaintSelection(selectedId: string) {
  for (const layer of layers.value) paintLayer(layer, selectedId);
}

function rangeAt(layer: SystemLayer, faceIndex: number): PartRange | undefined {
  const starts = layer.faceStarts;
  let low = 0;
  let high = starts.length - 1;
  while (low <= high) {
    const middle = (low + high) >> 1;
    const range = layer.ranges[middle];
    if (faceIndex < range.faceStart) high = middle - 1;
    else if (faceIndex >= range.faceStart + range.faceCount) low = middle + 1;
    else return range;
  }
  return undefined;
}

function neededSystems(): string[] {
  if (props.focusSystems.length) return props.focusSystems.filter((id) => partsBySystem.has(id));
  const hidden = new Set(props.hiddenSystems);
  return [...partsBySystem.keys()].filter((id) => !hidden.has(id));
}

/** Fetch and build only the systems the current view actually draws. */
async function ensureSystems(ids: string[]) {
  const active = scene.value;
  if (!active || !manifest) return;
  const missing = ids.filter((id) => !loadedSystems.has(id) && partsBySystem.has(id));
  if (!missing.length) return;

  let done = 0;
  for (const systemId of missing) {
    const chunkIndex = chunkIndexBySystem.get(systemId);
    if (chunkIndex === undefined) continue;
    const response = await fetch(manifest.chunks[chunkIndex].url);
    if (!response.ok) throw new Error(`模型分块读取失败（${response.status}）`);
    const buffer = await response.arrayBuffer();
    const layer = buildLayer(systemId, partsBySystem.get(systemId)!, buffer);
    active.add(layer.mesh);
    layers.value = [...layers.value, layer];
    loadedSystems.add(systemId);
    done += 1;
    progress.value = Math.round((done / missing.length) * 100);
    note.value = `正在载入三维解剖模型 ${done}/${missing.length}`;
  }
}

function applyVisibility() {
  const hidden = new Set(props.hiddenSystems);
  const focus = props.focusSystems;
  for (const layer of layers.value) {
    // A focused system is shown on its own so the group reads as a specimen;
    // otherwise the viewer falls back to the manual visibility toggles.
    layer.mesh.visible = focus.length ? focus.includes(layer.id) : !hidden.has(layer.id);
  }
  markDirty();
}

function boundsFor(systemIds: string[]): THREE.Box3 {
  const box = new THREE.Box3();
  for (const id of systemIds) {
    const single = systemBoundsMap.get(id);
    if (single) box.union(single);
  }
  return box;
}

function activeBounds(): THREE.Box3 {
  const focus = props.focusSystems;
  if (focus.length) {
    const box = boundsFor(focus);
    if (!box.isEmpty()) return box;
  }
  return overallBounds.clone();
}

function frameBox(box: THREE.Box3, animate: boolean) {
  const currentCamera = camera.value;
  const currentControls = controls.value;
  if (!currentCamera || !currentControls || box.isEmpty()) return;

  const center = box.getCenter(new THREE.Vector3());
  const radius = Math.max(box.getSize(new THREE.Vector3()).length() / 2, 0.02);
  const distance = (radius / Math.sin((currentCamera.fov * Math.PI) / 180 / 2)) * 1.14;
  const direction = new THREE.Vector3(0.52, 0.24, 1).normalize();
  const position = center.clone().addScaledVector(direction, distance);

  currentControls.minDistance = radius * 0.25;
  currentControls.maxDistance = radius * 14;
  currentCamera.near = Math.max(radius / 200, 0.004);
  currentCamera.far = radius * 80;
  currentCamera.updateProjectionMatrix();

  if (!animate) {
    currentCamera.position.copy(position);
    currentControls.target.copy(center);
    currentControls.update();
    markDirty();
    return;
  }

  cameraTween = {
    fromPosition: currentCamera.position.clone(),
    toPosition: position,
    fromTarget: currentControls.target.clone(),
    toTarget: center,
    startedAt: performance.now()
  };
  currentControls.enabled = false;
  markDirty();
}

function resetView() {
  frameBox(activeBounds(), true);
}

function pick(event: PointerEvent) {
  const currentCamera = camera.value;
  const currentRenderer = renderer.value;
  if (!currentCamera || !currentRenderer) return;

  const visible = layers.value.filter((layer) => layer.mesh.visible);
  if (!visible.length) return;

  const rect = currentRenderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, currentCamera);

  const hits = raycaster.intersectObjects(visible.map((layer) => layer.mesh), false);
  if (!hits.length) {
    emit('clear');
    return;
  }

  const hit = hits[0];
  const layer = layers.value.find((item) => item.mesh === hit.object);
  if (!layer) return;
  const range = rangeAt(layer, hit.faceIndex ?? 0);
  if (!range) return;

  emit('select', {
    id: range.id,
    name: range.name,
    system: range.system,
    systemName: system3DName(range.system)
  });
}

function onPointerDown(event: PointerEvent) {
  pointerDown = { x: event.clientX, y: event.clientY };
}

function onPointerUp(event: PointerEvent) {
  if (!pointerDown) return;
  const moved = Math.hypot(event.clientX - pointerDown.x, event.clientY - pointerDown.y);
  pointerDown = null;
  if (moved > 5) return;
  pick(event);
}

function resize() {
  const currentRenderer = renderer.value;
  const currentCamera = camera.value;
  const element = host.value;
  if (!currentRenderer || !currentCamera || !element) return;
  const width = Math.max(element.clientWidth, 1);
  const height = Math.max(element.clientHeight, 1);
  currentRenderer.setSize(width, height, false);
  currentCamera.aspect = width / height;
  currentCamera.updateProjectionMatrix();
  markDirty();
}

onMounted(async () => {
  const element = host.value;
  if (!element) return;

  try {
    const response = await fetch(ATLAS_3D_URL);
    if (!response.ok) throw new Error(`模型清单读取失败（${response.status}）`);
    manifest = (await response.json()) as Atlas3D;

    partsBySystem = new Map();
    for (const part of manifest.parts) {
      const bucket = partsBySystem.get(part.system);
      if (bucket) bucket.push(part);
      else partsBySystem.set(part.system, [part]);
    }
    chunkIndexBySystem = new Map(manifest.chunks.map((chunk, index) => [chunk.system, index]));

    overallBounds = new THREE.Box3();
    for (const part of manifest.parts) {
      overallBounds.expandByPoint(new THREE.Vector3().fromArray(part.bounds[0]));
      overallBounds.expandByPoint(new THREE.Vector3().fromArray(part.bounds[1]));
    }

    const active = new THREE.Scene();
    active.background = new THREE.Color('#101a1d');

    const activeCamera = new THREE.PerspectiveCamera(38, 1, 0.01, 100);
    const activeRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    activeRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    activeRenderer.outputColorSpace = THREE.SRGBColorSpace;
    element.appendChild(activeRenderer.domElement);
    activeRenderer.domElement.style.display = 'block';
    activeRenderer.domElement.style.width = '100%';
    activeRenderer.domElement.style.height = '100%';
    activeRenderer.domElement.setAttribute('role', 'img');
    activeRenderer.domElement.setAttribute(
      'aria-label',
      '可交互三维人体解剖模型。拖动旋转，滚轮缩放，点击结构查看详情。'
    );

    active.add(new THREE.AmbientLight(0xffffff, 1.15));
    const key = new THREE.DirectionalLight(0xfff2e4, 2.1);
    key.position.set(2.4, 3.6, 3.2);
    active.add(key);
    const fill = new THREE.DirectionalLight(0xbfd4e8, 1.05);
    fill.position.set(-3.2, 1.1, 1.8);
    active.add(fill);
    const rim = new THREE.DirectionalLight(0xffd9c2, 1.2);
    rim.position.set(-1.4, 2.2, -3.4);
    active.add(rim);

    const activeControls = new OrbitControls(activeCamera, activeRenderer.domElement);
    activeControls.enableDamping = true;
    activeControls.dampingFactor = 0.09;
    activeControls.rotateSpeed = 0.85;
    activeControls.zoomSpeed = 0.9;
    activeControls.autoRotateSpeed = 0.85;
    activeControls.autoRotate = props.autoRotate;
    activeControls.addEventListener('change', markDirty);

    scene.value = active;
    camera.value = activeCamera;
    renderer.value = activeRenderer;
    controls.value = activeControls;

    await ensureSystems(neededSystems());

    activeRenderer.domElement.addEventListener('pointerdown', onPointerDown);
    activeRenderer.domElement.addEventListener('pointerup', onPointerUp);

    observer = new ResizeObserver(resize);
    observer.observe(element);
    resize();

    const loop = () => {
      frameHandle = requestAnimationFrame(loop);
      if (cameraTween) {
        const ratio = Math.min((performance.now() - cameraTween.startedAt) / 460, 1);
        const eased = ratio * ratio * (3 - 2 * ratio);
        activeCamera.position.lerpVectors(cameraTween.fromPosition, cameraTween.toPosition, eased);
        activeControls.target.lerpVectors(cameraTween.fromTarget, cameraTween.toTarget, eased);
        if (ratio >= 1) {
          cameraTween = null;
          activeControls.enabled = true;
        }
        dirty = true;
      } else {
        activeControls.update();
      }
      if (!dirty) return;
      activeRenderer.render(active, activeCamera);
      dirty = false;
    };
    loop();

    loading.value = false;
    applyVisibility();
    frameBox(activeBounds(), false);
    repaintSelection(props.selectedId);

    const systemCounts: Record<string, number> = {};
    for (const [systemId, list] of partsBySystem) systemCounts[systemId] = list.length;
    emit('ready', { parts: manifest.parts.length, triangles: manifest.triangles, systems: systemCounts });
  } catch (error) {
    failed.value = error instanceof Error ? error.message : '三维模型加载失败';
    loading.value = false;
    emit('error', failed.value);
  }
});

onBeforeUnmount(() => {
  cancelAnimationFrame(frameHandle);
  observer?.disconnect();
  const currentRenderer = renderer.value;
  if (currentRenderer) {
    currentRenderer.domElement.removeEventListener('pointerdown', onPointerDown);
    currentRenderer.domElement.removeEventListener('pointerup', onPointerUp);
    currentRenderer.domElement.remove();
  }
  controls.value?.dispose();
  for (const layer of layers.value) {
    layer.geometry.dispose();
    layer.material.dispose();
  }
  currentRenderer?.dispose();
  scene.value = null;
  camera.value = null;
  renderer.value = null;
  controls.value = null;
  layers.value = [];
  loadedSystems.clear();
  systemBoundsMap.clear();
  manifest = null;
});

watch(() => props.selectedId, (value) => repaintSelection(value));
watch(() => props.hiddenSystems, () => {
  void ensureSystems(neededSystems()).then(applyVisibility);
}, { deep: true });
watch(() => props.focusSystems, () => {
  void ensureSystems(neededSystems()).then(() => {
    applyVisibility();
    frameBox(activeBounds(), true);
    repaintSelection(props.selectedId);
  });
}, { deep: true });
watch(() => props.autoRotate, (value) => {
  if (controls.value) controls.value.autoRotate = value;
  markDirty();
});

defineExpose({ resetView });
</script>

<template>
  <div class="anatomy-3d">
    <div ref="host" class="anatomy-3d-stage" />
    <div v-if="loading" class="anatomy-3d-overlay">
      <strong>{{ note }}</strong>
      <div class="anatomy-3d-bar"><i :style="{ width: progress + '%' }" /></div>
      <small>{{ progress }}%</small>
    </div>
    <div v-else-if="failed" class="anatomy-3d-overlay is-error">
      <strong>三维模型未能载入</strong>
      <small>{{ failed }}</small>
    </div>
    <div v-if="!loading && !failed" class="anatomy-3d-legend">
      <span v-for="system in ANATOMY_SYSTEMS_3D" :key="system.id">
        <i :style="{ background: system.color }" />{{ system.name }}
      </span>
    </div>
  </div>
</template>
