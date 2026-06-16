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
  const [directions, setDirections] = useState<any[]>([]);
  const [selectedDirection, setSelectedDirection] = useState<string | null>(null);
  const [characters, setCharacters] = useState<any[]>([]);

  const handleCreateProject = async () => {
    if (!name || !genre) {
      notify('\u8BF7\u586B\u5199\u9879\u76EE\u540D\u79F0\u548C\u7C7B\u578B', 'error');
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
      notify('\u8BF7\u7C98\u8D34\u6587\u98CE\u6837\u672C', 'error');
      return;
    }
    setLoading(true);
    try {
      const uploadResult = await stylesApi.uploadSample(projectId, styleSample);
      const result = await stylesApi.analyze(projectId, [uploadResult.sample_id], 'default-style');
      const styleId = 'style_id' in result ? (result as any).style_id : 'default-style';
      setStyleId(styleId);
      notify('\u6587\u98CE\u5206\u6790\u5B8C\u6210', 'success');
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
      setDirections(result.variants || []);
    } catch (e) {
      notify((e as Error).message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCharacters = async () => {
    if (!projectId || !selectedDirection) {
      notify('\u8BF7\u5148\u9009\u62E9\u65B9\u5411', 'error');
      return;
    }
    setLoading(true);
    try {
      const result = await bibleApi.generateCharacters(projectId, selectedDirection);
      setCharacters(result.characters || []);
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
      await bibleApi.generate(projectId, selectedDirection || '');
      await chaptersApi.plan(projectId, 1, '开场章节');
      notify('Bible \u751F\u6210\u5B8C\u6210\uFF0C\u5DF2\u521B\u5EFA\u7B2C 1 \u7AE0', 'success');
      navigate(`/project/${projectId}`);
    } catch (e) {
      notify((e as Error).message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { n: 1, label: '\u521B\u5EFA\u9879\u76EE' },
    { n: 2, label: '\u6587\u98CE\u5206\u6790' },
    { n: 3, label: 'Bible \u751F\u6210' },
  ];

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">\u521B\u5EFA\u65B0\u9879\u76EE</h1>

      <div className="flex items-center gap-2 mb-8">
        {steps.map((s, i) => (
          <div key={s.n} className="flex items-center">
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
            <label className="block text-sm font-medium text-gray-700 mb-1">\u9879\u76EE\u540D\u79F0 *</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm" placeholder="\u8F93\u5165\u5C0F\u8BF4\u540D\u79F0" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">\u7C7B\u578B *</label>
            <select value={genre} onChange={(e) => setGenre(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm">
              <option value="">\u9009\u62E9\u7C7B\u578B</option>
              <option value="\u90FD\u5E02">\u90FD\u5E02</option>
              <option value="\u7384\u5E7B">\u7384\u5E7B</option>
              <option value="\u4FEE\u4ED9">\u4FEE\u4ED9</option>
              <option value="\u79D1\u5E7B">\u79D1\u5E7B</option>
              <option value="\u60AC\u7591">\u60AC\u7591</option>
              <option value="\u5386\u53F2">\u5386\u53F2</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">\u521B\u610F\u7B80\u4ECB</label>
            <textarea value={idea} onChange={(e) => setIdea(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm" rows={4}
              placeholder="\u63CF\u8FF0\u4F60\u7684\u5C0F\u8BF4\u60F3\u6CD5..." />
          </div>
          <button onClick={handleCreateProject} disabled={loading}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:opacity-50">
            {loading ? '\u521B\u5EFA\u4E2D...' : '\u4E0B\u4E00\u6B65'}
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">\u7C98\u8D34\u6587\u98CE\u6837\u672C\u6587\u672C</label>
            <textarea value={styleSample} onChange={(e) => setStyleSample(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm font-mono" rows={8}
              placeholder="\u7C98\u8D34\u4F60\u5E0C\u671B\u6A21\u4EFF\u7684\u5C0F\u8BF4\u7247\u6BB5..." />
          </div>
          <button onClick={handleAnalyzeStyle} disabled={loading}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:opacity-50">
            {loading ? '\u5206\u6790\u4E2D...' : '\u5206\u6790\u6587\u98CE'}
          </button>
          {styleId && (
            <div className="text-sm text-green-700 bg-green-50 p-3 rounded">
              \u6587\u98CE\u5206\u6790\u5B8C\u6210\uFF0Cstyle_id: {styleId}
            </div>
          )}
          <button onClick={() => setStep(3)} disabled={!styleId}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:opacity-50">
            \u4E0B\u4E00\u6B65
          </button>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <div>
            <button onClick={handleGenerateDirections} disabled={loading}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50 text-sm">
              {loading ? '\u751F\u6210\u4E2D...' : '\u751F\u6210\u65B9\u5411\u53D8\u4F53'}
            </button>
          </div>

          {directions.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-medium text-sm">\u9009\u62E9\u4E00\u4E2A\u65B9\u5411</h3>
              {directions.map((d, i) => (
                <button key={i}
                  onClick={() => setSelectedDirection(d.direction_id || String(i))}
                  className={`w-full text-left border rounded p-3 text-sm ${
                    selectedDirection === (d.direction_id || String(i)) ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                  }`}>
                  <div className="font-medium">{d.title || `\u65B9\u5411 ${i + 1}`}</div>
                  <div className="text-gray-500 text-xs mt-1">{d.description || d.summary || ''}</div>
                </button>
              ))}
            </div>
          )}

          {selectedDirection && (
            <button onClick={handleGenerateCharacters} disabled={loading}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50 text-sm">
              \u751F\u6210\u89D2\u8272\u6982\u5FF5
            </button>
          )}

          {characters.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-medium text-sm">\u89D2\u8272\u6982\u5FF5</h3>
              {characters.map((c, i) => (
                <div key={i} className="border rounded p-3 text-sm">
                  <div className="font-medium">{c.name || `\u89D2\u8272 ${i + 1}`}</div>
                  <div className="text-gray-500 text-xs mt-1">{c.description || c.role || ''}</div>
                </div>
              ))}
            </div>
          )}

          <button onClick={handleGenerateBible} disabled={loading}
            className="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600 disabled:opacity-50">
            {loading ? '\u751F\u6210\u4E2D...' : '\u751F\u6210 Bible \u5E76\u5F00\u59CB'}
          </button>
        </div>
      )}
    </div>
  );
}