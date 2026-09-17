from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models import SkillCitation, SkillQuery, SkillResult


class AnatomySkills:
    """Read-only adapters; retrieved text is evidence, never executable instructions."""

    def __init__(self, root: Path, terms: Any, textbook: Any, graph: Any) -> None:
        self.terms, self.textbook, self.graph = terms, textbook, graph
        atlas_dir = root / 'frontend' / 'public' / 'anatomy'
        atlas = json.loads((atlas_dir / 'atlas.json').read_text(encoding='utf-8'))
        organs = json.loads((atlas_dir / 'organs.json').read_text(encoding='utf-8'))
        owners: dict[str, list[str]] = {}
        for group in organs['systems']:
            for organ in group['organs']:
                for part_id in organ['partIds']:
                    owners.setdefault(part_id, []).append(organ['name'])
        self.parts = [
            {
                'id': part['id'], 'name_en': part['name'],
                'name': terms.lookup(part['name']) or part['name'],
                'system': part['system'], 'organs': owners.get(part['id'], []),
            }
            for part in atlas['parts']
        ]
        self.handlers = {
            'anatomy_search': self.structure_search,
            'textbook_search': self.textbook_search,
            'graph_query': self.graph_query,
        }

    def structure_search(self, args: SkillQuery) -> SkillResult:
        q = args.query.strip().casefold()
        if args.part_id:
            matches = [part for part in self.parts if part['id'] == args.part_id]
        else:
            exact = [part for part in self.parts if q in {part['name'].casefold(), part['name_en'].casefold(), part['id'].casefold()}]
            matches = exact or [
                part for part in self.parts
                if q in part['name'].casefold() or q in part['name_en'].casefold()
                or any(q in organ.casefold() for organ in part['organs'])
            ]
        return SkillResult(
            skill_id='anatomy_search', status='success' if matches else 'empty',
            message=f'找到 {len(matches)} 个模型结构' if matches else '未找到匹配的模型结构',
            data={'items': matches[:8], 'total': len(matches)},
            citations=[SkillCitation(source='BodyParts3D 4.0', reference='本地 atlas.json / organs.json')] if matches else [],
        )

    def textbook_search(self, args: SkillQuery) -> SkillResult:
        part = next((part for part in self.parts if part['id'] == args.part_id), None) if args.part_id else None
        if args.part_id and part is None:
            return SkillResult(skill_id='textbook_search', status='empty', message='模型结构 ID 无效，不检索其他结构的教材')
        query = part['name'] if part else (self.terms.lookup(args.query.strip()) or args.query.strip())
        hit = self.textbook.search(query)
        if not hit:
            return SkillResult(skill_id='textbook_search', status='empty', message='未匹配到本地教材依据，请由教师核对或补充资料')
        return SkillResult(
            skill_id='textbook_search', status='success', message='已检索到教材片段',
            data={key: hit.get(key) for key in ('title', 'content', 'chapter', 'page')},
            citations=[SkillCitation(source=hit['source'], reference=hit['citation'], page=hit.get('page'))],
        )

    def graph_query(self, args: SkillQuery) -> SkillResult:
        q = args.query.strip().casefold()
        if args.part_id:
            seeds = [node for node in self.graph.nodes if node.get('anatomy_part_id') == args.part_id]
        else:
            exact = [node for node in self.graph.nodes if q in {node['id'].casefold(), self.graph.label(node).casefold(), node.get('label_en', '').casefold()}]
            seeds = exact or self.graph.search_nodes(args.query)
        if not seeds:
            return SkillResult(skill_id='graph_query', status='empty', message='当前解剖图谱没有匹配节点，不生成虚构关系')
        nodes: dict[str, dict] = {}
        edges: dict[tuple[str, str], dict] = {}
        for seed in seeds[:3]:
            neighborhood = self.graph.get_neighbors(seed['id'], depth=1)
            nodes[seed['id']] = {**seed, 'label': self.graph.label(seed)}
            for node in neighborhood['nodes']:
                nodes.setdefault(node['id'], node)
            for edge in neighborhood['edges']:
                edges[(edge['source'], edge['target'])] = edge
        selected = list(nodes.values())[:40]
        ids = {node['id'] for node in selected}
        return SkillResult(
            skill_id='graph_query', status='success', message='已查询一层结构归属关系（不代表空间毗邻关系）',
            data={
                'nodes': selected,
                'edges': [edge for edge in edges.values() if edge['source'] in ids and edge['target'] in ids][:60],
                'seed_ids': [node['id'] for node in seeds[:3]],
            },
            citations=[SkillCitation(source='BodyParts3D 4.0', reference='本地解剖图谱：系统 → 器官 → 精细结构')],
        )
