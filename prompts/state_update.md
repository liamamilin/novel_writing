你是一个小说状态更新专家。根据最终章节正文和状态标注，更新项目状态。

最终正文：
{{final_text}}

状态标注：
{{annotations}}

用户修改摘要：
{{diff_summary}}

当前角色状态：
{{current_characters}}

当前全局状态：
{{current_story_state}}

当前伏笔：
{{current_hooks}}

当前子线：
{{current_subplots}}

请输出 YAML，包含以下字段：
summary: 本章摘要（100字以内）
character_updates:
  - character_id: ...
    location: ...
    current_goal: ...
    current_emotion: ...
relationship_updates:
  - from: ...
    to: ...
    change: ...
timeline_update:
  start: ...
  end: ...
  duration: ...
  location: ...
new_hooks:
  - hook_id: ...
    content: ...
    type: mystery/tension/promise/emotional/power
    reader_patience: 8
triggered_hooks:
  - hook_id
resolved_hooks:
  - hook_id: ...
    resolution: ...
world_updates:
  - "新世界观信息"
subplot_advances:
  - subplot_id: ...
    advancement: ...
ability_changes:
  - character_id: ...
    ability: ...
    change: ...
next_chapter_suggestions:
  - "建议1"
  - "建议2"
  - "建议3"
bible_update_needed: false
bible_update_reasons: []

重要规则：
- 以状态标注为锚点，确认每个标注
- diff 中的用户修改优先级高于 AI 标注
- 角色不知道的信息不放在 known_information
- 伏笔状态只允许 open→triggered, open→resolved, 新增 open
