from __future__ import annotations
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from novel_runtime.config import Settings
from novel_runtime.db.database import Database
from novel_runtime.llm.provider import create_provider
from novel_runtime.llm.prompt_loader import PromptLoader
from novel_runtime.models.project import ProjectCreate
from novel_runtime.services.project_service import ProjectService
from novel_runtime.services.style_service import StyleService
from novel_runtime.services.bible_service import BibleService
from novel_runtime.services.context_service import ContextService
from novel_runtime.services.chapter_service import ChapterService
from novel_runtime.services.review_service import ReviewService
from novel_runtime.services.state_service import StateService
from novel_runtime.compiler.state_health_checker import StateHealthChecker
from novel_runtime.storage import strategy_storage, state_storage, subplot_storage


app = typer.Typer(name="novel", help="Novel Writing Runtime CLI")
style_app = typer.Typer()
bible_app = typer.Typer()
context_app = typer.Typer()
chapter_app = typer.Typer()
state_app = typer.Typer()

app.add_typer(style_app, name="style", help="文风资产管理")
app.add_typer(bible_app, name="bible", help="Bible 生成管理")
app.add_typer(context_app, name="context", help="上下文编译")
app.add_typer(chapter_app, name="chapter", help="章节操作")
app.add_typer(state_app, name="state", help="状态管理")

cache_app = typer.Typer()
app.add_typer(cache_app, name="cache", help="LLM 缓存管理")

console = Console()
def _get_services():
    settings = Settings()
    storage_base = Path(settings.storage_base_path)
    storage_base.mkdir(parents=True, exist_ok=True)
    db = Database(settings.db_path or str(storage_base / "nwr.db"))
    db.init_db()
    provider = create_provider(settings)
    loader = PromptLoader()
    project_svc = ProjectService(db, storage_base)
    return settings, provider, loader, project_svc, db, storage_base


@app.command()
def init(
    name: str = typer.Option(..., "--name", "-n", help="项目名称"),
    genre: str = typer.Option(..., "--genre", "-g", help="小说类型"),
    idea: str = typer.Option("", "--idea", "-i", help="创意描述"),
    target_reader: str = typer.Option("", "--target-reader", help="目标读者"),
    core_selling_point: str = typer.Option("", "--selling-point", help="核心卖点"),
    project_dir: str = typer.Option("", "--project", "-p", help="项目存储路径"),
):
    _, _, _, project_svc, _, _ = _get_services()
    if project_dir:
        project_svc.storage_base = Path(project_dir)
    create = ProjectCreate(
        project_name=name, genre=genre, idea=idea,
        target_reader=target_reader, core_selling_point=core_selling_point,
    )
    project = project_svc.create_project(create)
    console.print(f"✅ 项目 '{name}' 创建成功!")
    console.print(f"📁 项目路径: {project_svc.get_project_path(project.project_id)}")
    console.print("📋 下一步: 运行 novel style analyze 上传样本文本")


@style_app.command("analyze")
def style_analyze(
    project: str = typer.Option(..., "--project", "-p", help="项目ID"),
    sample: str = typer.Option(..., "--sample", "-s", help="样本文本文件路径"),
    name: str = typer.Option("文风", "--name", "-n", help="文风名称"),
    adversarial: bool = typer.Option(True, "--adversarial/--no-adversarial", help="运行对抗测试"),
):
    settings, provider, loader, project_svc, db, storage_base = _get_services()
    style_svc = StyleService(db, project_svc, provider, loader, settings)
    sample_text = Path(sample).read_text(encoding="utf-8")
    sample_id = style_svc.upload_sample(project, "样本", sample_text)
    style = style_svc.analyze_style_sync(project, [sample_id], name, adversarial)
    console.print("📊 文风分析完成!")
    console.print(f"🏷️  文风名称: {style.style_name}")
    console.print(f"📝 核心特征: {style.sentence_rhythm}, {style.dialogue_style}")
    console.print(f"✅ 对抗测试: {'通过' if adversarial else '跳过'}")
    console.print(f"📋 文风资产: {style.style_id}.yaml")


@bible_app.command("generate")
def bible_generate(
    project: str = typer.Option(..., "--project", "-p", help="项目ID"),
):
    _, provider, loader, project_svc, db, storage_base = _get_services()
    bible_svc = BibleService(db, project_svc, provider, loader)
    variants = bible_svc.generate_direction_variants(project)
    if not variants:
        console.print("❌ 生成方向变体失败")
        return
    console.print("📊 方向变体生成完成!")
    for i, v in enumerate(variants, 1):
        console.print(f"  {i}. {v.get('name', '')}: {v.get('core_selling_point', '')}")


@context_app.command("compile")
def context_compile(
    project: str = typer.Option(..., "--project", "-p", help="项目ID"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="章节号"),
    goal: str = typer.Option("", "--goal", "-g", help="本章目标"),
):
    _, provider, loader, project_svc, _, _ = _get_services()
    ctx_svc = ContextService(project_svc, provider, loader)
    result = ctx_svc.compile_context(project, chapter, goal)
    console.print("📚 上下文编译完成!")
    console.print(f"📄 Context Pack: {result.get('context_pack_path', '')}")
    console.print(f"⚠️  健康告警: {result.get('health_issues', 0)} 条")


@chapter_app.command("plan")
def chapter_plan(
    project: str = typer.Option(..., "--project", "-p", help="项目ID"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="章节号"),
):
    _, provider, loader, project_svc, _, _ = _get_services()
    ctx_svc = ContextService(project_svc, provider, loader)
    ch_svc = ChapterService(project_svc, ctx_svc, provider, loader)
    result = ch_svc.generate_plan(project, chapter)
    if result.get("plan_path"):
        console.print(f"✅ 章节规划完成! → {result['plan_path']}")
        console.print(f"📊 节奏类型: {result.get('rhythm_type', '')}")
    else:
        console.print(f"❌ 规划失败: {result.get('errors', [])}")


@chapter_app.command("draft")
def chapter_draft(
    project: str = typer.Option(..., "--project", "-p", help="项目ID"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="章节号"),
):
    _, provider, loader, project_svc, _, _ = _get_services()
    ctx_svc = ContextService(project_svc, provider, loader)
    ch_svc = ChapterService(project_svc, ctx_svc, provider, loader)
    result = ch_svc.generate_draft(project, chapter)
    if result.get("draft_path"):
        console.print(f"✅ 草稿生成完成! → {result['draft_path']}")
    else:
        console.print(f"❌ 生成失败: {result.get('errors', [])}")


@chapter_app.command("polish")
def chapter_polish(
    project: str = typer.Option(..., "--project", "-p", help="项目ID"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="章节号"),
):
    _, provider, loader, project_svc, _, _ = _get_services()
    ctx_svc = ContextService(project_svc, provider, loader)
    ch_svc = ChapterService(project_svc, ctx_svc, provider, loader)
    result = ch_svc.polish_draft(project, chapter)
    if result.get("styled_draft_path"):
        console.print(f"✅ 文风润色完成! → {result['styled_draft_path']}")
    else:
        console.print(f"❌ 润色失败: {result.get('errors', [])}")


@chapter_app.command("review")
def chapter_review(
    project: str = typer.Option(..., "--project", "-p", help="项目ID"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="章节号"),
):
    _, provider, loader, project_svc, _, _ = _get_services()
    review_svc = ReviewService(project_svc, provider, loader)
    result = review_svc.review_chapter(project, chapter)
    console.print("✅ 审查完成!")
    if result.get("has_critical_issues"):
        console.print("⚠️  存在严重问题，建议修复")


@chapter_app.command("approve")
def chapter_approve(
    project: str = typer.Option(..., "--project", "-p", help="项目ID"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="章节号"),
    final_text: str = typer.Option("", "--final-text", "-f", help="最终正文文件路径"),
):
    _, provider, loader, project_svc, _, storage_base = _get_services()
    if final_text:
        text = Path(final_text).read_text(encoding="utf-8")
    else:
        text = typer.prompt("请输入最终正文")
    final_path = project_svc.get_project_path(project) / "chapters" / f"chapter_{chapter:03d}" / "final.md"
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(text, encoding="utf-8")
    chapter_obj = project_svc.get_chapter(project, chapter)
    chapter_obj.status = "approved"
    from novel_runtime.storage.project_storage import ProjectStorage
    p = project_svc.get_project(project)
    ProjectStorage(storage_base).save_chapter(p, chapter_obj)
    console.print("✅ 章节确认完成!")
    console.print(f"📄 final.md 已保存: {final_path}")


@state_app.command("update")
def state_update(
    project: str = typer.Option(..., "--project", "-p", help="项目ID"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="章节号"),
):
    _, provider, loader, project_svc, _, _ = _get_services()
    state_svc = StateService(project_svc, provider, loader)
    result = state_svc.update_state(project, chapter)
    console.print("✅ 状态更新完成!")
    if result.get("snapshot_path"):
        console.print(f"📸 快照: {result['snapshot_path']}")
    console.print(f"📄 更新文件: {', '.join(result.get('updated_files', []))}")


@state_app.command("rollback")
def state_rollback(
    project: str = typer.Option(..., "--project", "-p", help="项目ID"),
    target_chapter: int = typer.Option(..., "--target-chapter", "-t", help="目标章节号"),
):
    if not typer.confirm(f"⚠️  确认回滚到第 {target_chapter} 章?"):
        return
    _, provider, loader, project_svc, _, _ = _get_services()
    state_svc = StateService(project_svc, provider, loader)
    result = state_svc.rollback_state(project, target_chapter)
    console.print(f"✅ 状态已回滚到第 {result['restored_to_chapter']} 章")


@app.command()
def health(
    project: str = typer.Option(..., "--project", "-p", help="项目ID"),
    chapter: int = typer.Option(1, "--chapter", "-c", help="章节号"),
):
    _, _, _, project_svc, _, _ = _get_services()
    project_path = project_svc.get_project_path(project)
    strategy = strategy_storage.load_strategy(project_path)
    checker = StateHealthChecker()
    report = checker.check(project_path, chapter, strategy)
    console.print("📊 状态健康检查")
    for issue in report.issues:
        icon = "🔴" if issue.severity == "critical" else "🟡" if issue.severity == "warning" else "🟢"
        console.print(f"  {icon} {issue.description}")
    if not report.issues:
        console.print("✅ 所有检查通过")


@app.command()
def next_suggest(
    project: str = typer.Option(..., "--project", "-p", help="项目ID"),
):
    _, _, _, project_svc, _, _ = _get_services()
    project_path = project_svc.get_project_path(project)
    hooks = [h for h in state_storage.load_hooks(project_path) if h.status == "open"]
    subplots = [s for s in subplot_storage.load_subplots(project_path) if s.status != "resolved"]
    console.print("📋 下一章建议:")
    for i, h in enumerate(hooks[:3], 1):
        console.print(f"  {i}. {h.content[:50]} (优先级: {h.priority})")
    for i, s in enumerate(subplots[:2], len(hooks[:3]) + 1):
        console.print(f"  {i}. 推进子线: {s.name}")


if __name__ == "__main__":
    app()


@cache_app.command("stats")
def cache_stats():
    settings = Settings()
    if not settings.llm_cache_enabled:
        console.print("❌ LLM 缓存未启用 (设 NWR_LLM_CACHE_ENABLED=true)")
        return
    from novel_runtime.llm.cache import LLMCache
    cache_path = settings.llm_cache_path or str(Path(settings.storage_base_path) / "llm_cache.db")
    cache = LLMCache(db_path=cache_path, ttl=settings.llm_cache_ttl)
    s = cache.stats()
    console.print(f"📊 LLM 缓存统计")
    console.print(f"  总条目: {s['total_entries']}")
    console.print(f"  总命中: {s['total_hits']}")


@cache_app.command("clear")
def cache_clear():
    settings = Settings()
    if not settings.llm_cache_enabled:
        console.print("❌ LLM 缓存未启用 (设 NWR_LLM_CACHE_ENABLED=true)")
        return
    if not typer.confirm("⚠️  确认清空所有 LLM 缓存?"):
        return
    from novel_runtime.llm.cache import LLMCache
    cache_path = settings.llm_cache_path or str(Path(settings.storage_base_path) / "llm_cache.db")
    cache = LLMCache(db_path=cache_path, ttl=settings.llm_cache_ttl)
    count = cache.clear()
    console.print(f"✅ 已清空 {count} 条缓存条目")
