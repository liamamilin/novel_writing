你是一个专业的文风分析专家。分析以下样本文本，提取其文风特征。

样本文本：
{{samples}}

文风名称：{{style_name}}

请分析以下维度，输出 YAML 格式：

1. narration: 叙述视角（第一人称/第三人称/全知/贴身视角）
2. sentence_rhythm: 句式节奏（短句为主/中等/长句为主/混合）
3. dialogue_style: 对白风格（直接冲突型/含蓄型/信息型/幽默型）
4. description_density: 描写密度（环境描写比例，动作描写比例，心理描写比例）
5. emotion_curve: 情绪曲线（铺垫→爆发→释放，或具体描述）
6. conflict_pattern: 冲突推进方式（外部冲突驱动/内部驱动/混合）
7. chapter_opening: 章节开头方式（冲突开场/悬念开场/日常开场/环境开场）
8. chapter_ending: 章节结尾方式（反转/悬念/情绪收束/信息揭示）
9. scene_density: 场景节奏（每多少字出现一次动作或冲突变化）
10. avoid: 禁用表达模式列表（如"大段设定说明，连续心理独白，重复口癖，过度形容"等）
11. conditional_rules: 条件文风规则列表，每条包含:
    - condition: 场景类型（fight_scene/emotional_scene/dialogue_scene/exposition_scene/climax_scene）
    - adjustments: 文风调整（如 sentence_rhythm: "极短句"，description_density: "动作描写为主"）

重要要求：
- 不复制原文表达，只提取抽象特征
- 至少为战斗场景和情感场景各写一条条件规则
- avoid 列表至少包含3个禁用表达
- 输出必须是纯 YAML 格式，不要包含其他内容
