import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import { useUIStore } from '../stores/uiStore';
import { stylesApi } from '../api/styles';
import { bibleApi } from '../api/bible';
import { chaptersApi } from '../api/chapters';

type Step = 1 | 2 | 3;

export function ProjectCreate() {
  const navigate = useNavigate();
  const createProject = useProjectStore((s) => s.createProject);
  const selectProject = useProjectStore((s) => s.selectProject);
  const notify = useUIStore((s) => s.notify);

  const [step, setStep] = useState<Step>(1);
  const [loading, setLoading] = useState(false);
  const [projectId, setProjectId] = useState<string | null>(null);

  const [name, setName] = useState('');
  const [genre, setGenre] = useState('');
  const [idea, setIdea] = useState('');
  const [styleSample, setStyleSample] = useState('');
  const [styleId, setStyleId] = useState<string | null>(null);
  const [directions, setDirections] = useState<{ direction_id: string; title: string; description?: string; summary?: string }[]>([]);
  const [selectedDirection, setSelectedDirection] = useState<string | null>(null);
  const [characters, setCharacters] = useState<{ name: string; description?: string; role?: string }[]>([]);

  const handleCreateProject = async () => {
    if (!name || !genre) {
      notify('请填写项目名称和类型', 'error');
      return;
    }
    setLoading(true);
    try {
      const id = await createProject({ project_name: name, genre, idea });
      setProjectId(id);
      await selectProject(id);
      setStep(2);
    } catch (e) {
      notify((e as Error).message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeStyle = async () => {
    if (!projectId || !styleSample) {
      notify('请粘贴文风样本', 'error');
      return;
    }
    setLoading(true);
    try {
      const uploadResult = await stylesApi.uploadSample(projectId, styleSample);
      const result = await stylesApi.analyzeSync(projectId, [uploadResult.sample_id], 'default-style');
      const sid = result.style_id || 'default-style';
      setStyleId(sid);
      notify('文风分析完成', 'success');
      setStep(3);
    } catch (e) {
      notify((e as Error).message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDirections = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const result = await bibleApi.direction(projectId, idea, genre);
      setDirections((result.variants || []) as any);
    } catch (e) {
      notify((e as Error).message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCharacters = async () => {
    if (!projectId || !selectedDirection) {
      notify('请先选择方向', 'error');
      return;
    }
    setLoading(true);
    try {
      const result = await bibleApi.generateCharacters(projectId, selectedDirection);
      setCharacters((result.characters || []) as any);
    } catch (e) {
      notify((e as Error).message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateBible = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      await bibleApi.generate(projectId, selectedDirection || '', characters);
      await chaptersApi.plan(projectId, 1, '开场章节');
      notify('Bible 生成完成，已创建第 1 章', 'success');
      navigate(`/project/${projectId}?ch=1&asset=chapter`);
    } catch (e) {
      notify((e as Error).message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { n: 1, label: '创建项目', hint: '填写项目名称、类型和创意' },
    { n: 2, label: '文风分析', hint: '上传样本文本，AI 自动提取写作风格特征' },
    { n: 3, label: '方向+角色', hint: '生成方向变体 → 选择方向 → 生成角色概念' },
    { n: 4, label: 'Bible 生成', hint: '生成完整 Bible（人物/世界观/卷大纲）→ 自动创建第一章' },
  ];

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">创建新项目</h1>

      <div className="flex items-center gap-2 mb-8">
        {steps.map((s, i) => (
            <div key={s.n} className="flex items-center" title={s.hint}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step >= s.n ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-500'
            }`}>
              {s.n}
            </div>
            <span className={`ml-2 text-sm ${step >= s.n ? 'text-gray-900' : 'text-gray-400'}`}>
              {s.label}
            </span>
            {i < steps.length - 1 && <div className="w-8 h-0.5 bg-gray-300 mx-2" />}
          </div>
        ))}
      </div>

      {step === 1 && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">项目名称 *</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm" placeholder="输入小说名称" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">类型 *</label>
            <select value={genre} onChange={(e) => setGenre(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm">
              <option value="">选择类型</option>
              <option value="都市">都市</option>
              <option value="玄幻">玄幻</option>
              <option value="修仙">修仙</option>
              <option value="科幻">科幻</option>
              <option value="悬疑">悬疑</option>
              <option value="历史">历史</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">创意简介</label>
            <textarea value={idea} onChange={(e) => setIdea(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm" rows={4}
              placeholder="描述你的小说想法..." />
          </div>
          <div className="flex gap-2">
            <button onClick={() => navigate('/')}
              className="px-6 py-2 rounded text-gray-600 border border-gray-300 hover:bg-gray-50">
              返回
            </button>
            <button onClick={handleCreateProject} disabled={loading}
              className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:opacity-50">
              {loading ? '创建中...' : '下一步'}
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              粘贴文风样本文本
              <span className="ml-1 text-xs text-gray-400" title="上传一段你喜欢的写作风格的样本，AI 会分析其文风特征">?</span>
            </label>
            <textarea value={styleSample} onChange={(e) => setStyleSample(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm font-mono" rows={8}
              placeholder="粘贴你希望模仿的小说片段..." />
            <details className="mt-2">
              <summary className="text-xs text-blue-500 cursor-pointer hover:text-blue-700">想不到样本？点这里使用示例文本</summary>
              <div className="mt-2 text-xs text-gray-600 bg-gray-50 p-3 rounded border">
                <p>林云推开大门，刺眼的灯光倾泻而下。全场安静了三秒。</p>
                <p className="mt-1">他扫视了一圈。东边是赵家的包间，西边是李家的，中间主位上坐着一个戴着玉扳指的老人——云海市拍卖行的掌舵人。</p>
                <p className="mt-1">"来了？"老人抬眼。</p>
                <p className="mt-1">"来了。"林云淡淡应道，在最后一排坐下。</p>
                <button
                  onClick={() => setStyleSample('林云推开大门，刺眼的灯光倾泻而下。全场安静了三秒。\n\n他扫视了一圈。东边是赵家的包间，西边是李家的，中间主位上坐着一个戴着玉扳指的老人——云海市拍卖行的掌舵人。\n\n"来了？"老人抬眼。\n\n"来了。"林云淡淡应道，在最后一排坐下。')}
                  className="mt-2 text-blue-500 hover:text-blue-700"
                >
                  使用此样本
                </button>
              </div>
            </details>
          </div>
          <div className="flex gap-2">
            <button onClick={() => setStep(1)}
              className="px-6 py-2 rounded text-gray-600 border border-gray-300 hover:bg-gray-50">
              上一步
            </button>
            <button onClick={handleAnalyzeStyle} disabled={loading}
              className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:opacity-50">
              {loading ? '分析中...' : '分析文风'}
            </button>
          </div>
          {styleId && (
            <div className="text-sm text-green-700 bg-green-50 p-3 rounded">
              文风分析完成，style_id: {styleId}
            </div>
          )}
          <button onClick={() => setStep(3)} disabled={!styleId}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:opacity-50">
            下一步
          </button>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <div>
            <button onClick={handleGenerateDirections} disabled={loading}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50 text-sm">
              {loading ? '生成中...' : '生成方向变体'}
            </button>
          </div>

          {directions.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-medium text-sm">选择一个方向</h3>
              {directions.map((d, i) => (
                <button key={i}
                  onClick={() => setSelectedDirection(d.direction_id || String(i))}
                  className={`w-full text-left border rounded p-3 text-sm ${
                    selectedDirection === (d.direction_id || String(i)) ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                  }`}>
                  <div className="font-medium">{d.title || `方向 ${i + 1}`}</div>
                  <div className="text-gray-500 text-xs mt-1">{d.description || d.summary || ''}</div>
                </button>
              ))}
            </div>
          )}

          {selectedDirection && (
            <button onClick={handleGenerateCharacters} disabled={loading}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50 text-sm">
              生成角色概念
            </button>
          )}

          {characters.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-medium text-sm">角色概念</h3>
              {characters.map((c, i) => (
                <div key={i} className="border rounded p-3 text-sm">
                  <div className="font-medium">{c.name || `角色 ${i + 1}`}</div>
                  <div className="text-gray-500 text-xs mt-1">{c.description || c.role || ''}</div>
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-2 items-center">
            <button onClick={() => setStep(2)}
              className="px-6 py-2 rounded text-gray-600 border border-gray-300 hover:bg-gray-50">
              上一步
            </button>
            <button onClick={handleGenerateBible} disabled={loading}
              className="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600 disabled:opacity-50">
              {loading ? '生成中...' : '生成 Bible 并开始'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}