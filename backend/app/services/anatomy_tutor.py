from __future__ import annotations

import re
from uuid import uuid4

from ..models import AgentAction, AgentChatRequest, AgentChatResponse, AuthUser, SkillQuery, WorkflowStep
from .skill_registry import CATALOG, SkillRegistry


class AnatomyTutor:
    """Bounded local planning, not an autonomous LLM or a clinical advisor."""

    def __init__(self, registry: SkillRegistry) -> None:
        self.registry = registry

    def run(self, request: AgentChatRequest, user: AuthUser) -> AgentChatResponse:
        notes = ['仅用于解剖教学，不提供个人诊断或治疗建议。', '检索内容作为资料展示，不作为系统指令执行。']
        if re.search(r'(我|患者|病人).{0,16}(疼|痛|出血|发烧|肿|症状)|吃什么药|怎么治疗|帮我诊断', request.message):
            return AgentChatResponse(
                intent='education_safety', action='show_results', target_module='anatomy',
                reply='这里提供解剖教学资料，不能判断个人病情或推荐治疗。涉及身体不适请咨询专业医务人员。',
                safety_notes=notes, execution_mode='local_skill_planner',
            )
        args = request.context
        if args is None:
            match = re.search(r'结构：([^\n；]+)', request.message)
            query = match.group(1).strip() if match else request.message.strip()[:200]
            args = SkillQuery(query=query)
        args = args.model_copy(update={'query': args.query.strip()})
        if not args.query:
            return AgentChatResponse(intent='anatomy_teaching', action='show_results', target_module='anatomy', reply='请先选择或输入一个解剖结构。', execution_mode='local_skill_planner')
        plan = ['anatomy_search', 'textbook_search']
        if any(word in request.message for word in ('关系', '图谱', '归属', '组成', '考试', '系统')):
            plan.append('graph_query')
        run_id = uuid4().hex
        results = [self.registry.invoke(skill_id, args, user.account, user.role, run_id) for skill_id in plan]
        citations = []
        for result in results:
            for citation in result.citations:
                if citation not in citations:
                    citations.append(citation)
        structure_result = results[0]
        structures = structure_result.data.get('items', []) if structure_result.status == 'success' else []
        textbook_result = results[1]
        paragraphs = [f'{args.query} · 解剖教学检索']
        actions = []
        cards = []
        if structures:
            for part in structures[:3]:
                cards.append({'kind': '模型结构', 'title': part['name'], 'summary': '、'.join(part['organs']) or part['system'], 'target': part['id']})
                actions.append(AgentAction(type='highlight_structure', target=part['id'], label=part['name']))
            paragraphs.append('模型匹配：' + '、'.join(part['name'] for part in structures[:3]) + '。')
        else:
            paragraphs.append(structure_result.message + '。')
        if textbook_result.status == 'success':
            paragraphs.append('教材片段：\n' + str(textbook_result.data.get('content') or '')[:1200])
            if textbook_result.citations:
                paragraphs.append('依据：' + textbook_result.citations[0].reference)
            actions.append(AgentAction(type='open_textbook', target=structures[0]['name'] if structures else args.query, label='教材详解'))
        else:
            paragraphs.append(textbook_result.message + '。不使用模型常识补写未核实的教材结论。')
        graph_result = next((result for result in results if result.skill_id == 'graph_query'), None)
        learning_path = []
        if graph_result:
            if graph_result.status == 'success':
                data = graph_result.data
                labels = {node['id']: node.get('label') or node['id'] for node in data['nodes']}
                relations = [f"{labels[edge['source']]} —{edge['relation']}→ {labels[edge['target']]}" for edge in data['edges'][:5]]
                paragraphs.append('图谱归属关系：\n' + '\n'.join(relations))
                paragraphs.append('当前图谱只表达结构归属，不能据此推断空间毗邻、血供或神经支配。')
                learning_path = [labels[node_id] for node_id in data['seed_ids'] if node_id in labels]
                actions.append(AgentAction(type='open_graph', target=args.query, label='查看图谱'))
            else:
                paragraphs.append(graph_result.message + '。')
        paragraphs.append(notes[0])
        return AgentChatResponse(
            intent='anatomy_teaching', action='explain_structure', target_module='anatomy',
            reply='\n\n'.join(paragraphs), result_cards=cards, learning_path=learning_path,
            workflow_trace=[WorkflowStep(id=result.call_id, name=CATALOG[result.skill_id]['name'], agent='AnatomyTutor', status=result.status, detail=result.message) for result in results],
            safety_notes=notes, execution_mode='local_skill_planner', skill_results=results,
            citations=citations, actions=actions,
        )
