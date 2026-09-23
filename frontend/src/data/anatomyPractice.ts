import {
  anatomyAtlasNodes,
  type AnatomyAtlasHotspot,
  type AnatomyAtlasNode
} from './anatomyAtlas';

interface PracticeDefinition {
  nodeId: string;
  hotspotId?: string;
  target?: Omit<AnatomyAtlasHotspot, 'id'> & { id: string };
}

export interface AnatomyPracticeTarget {
  node: AnatomyAtlasNode;
  hotspot: AnatomyAtlasHotspot;
  label: string;
  targetId: string;
}

const definitions: Record<string, PracticeDefinition> = {
  heart_position: { nodeId: 'heart_chambers', hotspotId: 'hs_ra' },
  aorta_course: { nodeId: 'heart_blood_flow_detail', hotspotId: 'flow_aorta_hs' },
  pulmonary_artery: { nodeId: 'heart_blood_flow_detail', hotspotId: 'flow_pulmonary_hs' },
  trachea: { nodeId: 'trachea_detail', hotspotId: 'trachea_cartilage_hs' },
  left_lung: { nodeId: 'respiratory_overview', hotspotId: 'resp_lungs_hs' },
  right_lung: { nodeId: 'respiratory_overview', hotspotId: 'resp_lungs_hs' },
  liver_position: { nodeId: 'liver_detail', hotspotId: 'right_lobe_hs' },
  stomach_position: {
    nodeId: 'digestive_overview',
    target: { id: 'stomach_target', label: '胃', x: 63, y: 44, width: 14, height: 14 }
  },
  pancreas_position: { nodeId: 'pancreas_biliary_detail', hotspotId: 'pancreas_body_hs' },
  gallbladder_position: { nodeId: 'gallbladder_detail', hotspotId: 'gallbladder_hs' },
  small_intestine: { nodeId: 'small_intestine_detail', hotspotId: 'jejunum_hs' },
  large_intestine: { nodeId: 'large_intestine_detail', hotspotId: 'colon_transverse' },
  kidney_position: { nodeId: 'urinary_overview', hotspotId: 'kidney_medulla_hs' },
  ureter_course: { nodeId: 'urinary_tract_detail', hotspotId: 'urinary_ureters_hs' },
  bladder_position: { nodeId: 'urinary_tract_detail', hotspotId: 'urinary_bladder_hs' },
  brain_position: { nodeId: 'brain_lobes_detail', hotspotId: 'frontal_lobe_hs' },
  cerebellum_position: {
    nodeId: 'nervous_overview',
    target: { id: 'cerebellum_target', label: '小脑', x: 68, y: 82, width: 22, height: 18 }
  },
  brainstem_position: { nodeId: 'brainstem_detail', hotspotId: 'midbrain_hs' },
  spinal_cord: { nodeId: 'spinal_cord_section_detail', hotspotId: 'white_columns_hs' }
};

function normaliseName(value: string) {
  return value
    .replace(/[（(].*?[）)]/g, '')
    .replace(/\s+/g, '')
    .trim();
}

function findHotspot(node: AnatomyAtlasNode, structureName: string) {
  const needle = normaliseName(structureName);
  if (!needle) return undefined;
  const byLabel = node.hotspots.find((hotspot) => {
    const label = normaliseName(hotspot.label);
    return label.includes(needle) || needle.includes(label);
  });
  if (byLabel) return byLabel;
  const structure = node.structures.find((item) => {
    const name = normaliseName(item.name);
    return name.includes(needle) || needle.includes(name);
  });
  if (!structure) return undefined;
  return node.hotspots.find((hotspot) => hotspot.structure_id === structure.id) ?? undefined;
}

export function resolveAnatomyPracticeTarget(
  exerciseId: string,
  structureName = ''
): AnatomyPracticeTarget | null {
  const definition = definitions[exerciseId];
  if (!definition) return null;
  const node = anatomyAtlasNodes.find((item) => item.id === definition.nodeId);
  if (!node) return null;
  const matched = findHotspot(node, structureName);
  const configured = definition.target ?? node.hotspots.find((hotspot) => hotspot.id === definition.hotspotId);
  const hotspot = matched ?? configured ?? node.hotspots.find((item) => item.width < 100 && item.height < 100);
  if (!hotspot) return null;
  return {
    node,
    hotspot,
    label: hotspot.label,
    targetId: hotspot.structure_id ?? hotspot.id
  };
}
