<script setup lang="ts">
import { computed } from 'vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const props = withDefaults(defineProps<{
  content?: string;
}>(), {
  content: ''
});

marked.setOptions({
  gfm: true,
  breaks: true
});

DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A') {
    node.setAttribute('target', '_blank');
    node.setAttribute('rel', 'noopener noreferrer');
  }
});

const html = computed(() => {
  const source = props.content.trim();
  if (!source) return '';
  return DOMPurify.sanitize(marked.parse(source) as string);
});
</script>

<template>
  <div v-if="html" class="markdown-content" v-html="html" />
</template>

<style scoped>
.markdown-content { color: #33454f; font-size: 14px; line-height: 1.78; overflow-wrap: anywhere; }
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4) { margin: 18px 0 9px; color: #16313a; line-height: 1.38; }
.markdown-content :deep(h1) { font-size: 21px; }
.markdown-content :deep(h2) { font-size: 18px; }
.markdown-content :deep(h3) { font-size: 16px; }
.markdown-content :deep(h4) { font-size: 14px; }
.markdown-content :deep(p) { margin: 8px 0; }
.markdown-content :deep(ul),
.markdown-content :deep(ol) { margin: 8px 0; padding-left: 22px; }
.markdown-content :deep(li) { margin: 4px 0; }
.markdown-content :deep(strong) { color: #153e3a; font-weight: 800; }
.markdown-content :deep(blockquote) { margin: 12px 0; padding: 8px 12px; border-left: 3px solid #4ca99c; background: #eef8f5; color: #4d686a; }
.markdown-content :deep(table) { width: 100%; margin: 12px 0; border-collapse: collapse; font-size: 13px; }
.markdown-content :deep(th),
.markdown-content :deep(td) { padding: 8px 10px; border: 1px solid #cfe0dd; text-align: left; vertical-align: top; }
.markdown-content :deep(th) { background: #e8f4f1; color: #205b55; font-weight: 800; }
.markdown-content :deep(tr:nth-child(even) td) { background: #f8fbfa; }
.markdown-content :deep(code) { padding: 2px 5px; border-radius: 4px; background: #edf3f2; color: #9b4b3f; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 12px; }
.markdown-content :deep(pre) { overflow-x: auto; padding: 11px 13px; border-radius: 6px; background: #102a2d; color: #e6f2ef; }
.markdown-content :deep(pre code) { padding: 0; background: transparent; color: inherit; }
.markdown-content :deep(a) { color: #087f78; text-decoration: underline; text-underline-offset: 2px; }
.markdown-content :deep(hr) { margin: 16px 0; border: 0; border-top: 1px solid #dbe7e5; }
</style>
