'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Upload, FileText, TrendingUp, Mic, CheckCircle,
  Loader2, Briefcase, MapPin, ExternalLink, Zap,
  ChevronRight, Target, Brain, Globe, Star, Send,
  RefreshCw, CheckSquare, Award, Trash2, Copy, X,
  PenLine, BarChart2, ShieldCheck, FileDown
} from 'lucide-react';

// ── Types ────────────────────────────────────────────────────────────────────
type PipelineStatus = 'idle' | 'streaming' | 'done' | 'error';
type AgentStatus = 'waiting' | 'running' | 'done' | 'error';
type JobStatus = 'saved' | 'applied' | 'interview' | 'offer' | 'rejected' | null;

interface AgentState  { status: AgentStatus; data: any; }
interface PipelineState {
  resume: AgentState; matching: AgentState; gaps: AgentState;
  interview: AgentState; career: AgentState;
}
interface InterviewQA {
  question: string; answer: string;
  evaluation: { score: number; feedback: string; better_answer_hint: string; stars: number } | null;
  evaluating: boolean;
}
interface JobTrack { status: JobStatus; note: string; }
interface CoverLetter {
  job: any;
  letter: string;
  wordCount: number;
  loading: boolean;
  tone: 'professional' | 'friendly' | 'confident';
}
interface ATSScore {
  ats_score: number;
  overall_score: number;
  strengths: string[];
  suggestions: string[];
  verdict: string;
}

const EMPTY_PIPELINE: PipelineState = {
  resume:    { status: 'waiting', data: null },
  matching:  { status: 'waiting', data: null },
  gaps:      { status: 'waiting', data: null },
  interview: { status: 'waiting', data: null },
  career:    { status: 'waiting', data: null },
};

const STORAGE_KEY = 'jobmatch_analysis_v2';
const TRACKER_KEY = 'jobmatch_tracker_v2';

const AGENT_META: Record<string, { label: string; color: string }> = {
  resume:    { label: 'Resume Intelligence', color: 'blue' },
  matching:  { label: 'Semantic Matching',   color: 'violet' },
  gaps:      { label: 'Skill Graph',         color: 'amber' },
  interview: { label: 'Mock Interview',      color: 'green' },
  career:    { label: 'Career War Room',     color: 'pink' },
};

const JOB_STATUSES: { id: JobStatus; label: string; color: string }[] = [
  { id: 'saved',     label: 'Saved',      color: 'bg-slate-700 text-slate-300' },
  { id: 'applied',   label: 'Applied',    color: 'bg-blue-600 text-white' },
  { id: 'interview', label: 'Interview',  color: 'bg-violet-600 text-white' },
  { id: 'offer',     label: '🎉 Offer',   color: 'bg-green-600 text-white' },
  { id: 'rejected',  label: 'Rejected',   color: 'bg-red-700 text-white' },
];

// ── Star Rating ──────────────────────────────────────────────────────────────
function Stars({ n }: { n: number }) {
  return (
    <div className="flex gap-0.5">
      {[1,2,3,4,5].map(i => (
        <Star key={i} size={14}
          className={i <= n ? 'text-yellow-400 fill-yellow-400' : 'text-slate-700'} />
      ))}
    </div>
  );
}

// ── Agent Pill ───────────────────────────────────────────────────────────────
function AgentPill({ id, state }: { id: string; state: AgentState }) {
  const meta = AGENT_META[id];
  const base = 'flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-bold uppercase tracking-widest transition-all duration-300';
  const cls = state.status === 'running'
    ? `${base} text-blue-400 border-blue-500/40 bg-blue-600/10 animate-pulse`
    : state.status === 'done'
    ? `${base} text-${meta.color}-400 border-${meta.color}-500/30 bg-${meta.color}-600/10`
    : state.status === 'error'
    ? `${base} text-red-400 border-red-500/30 bg-red-600/10`
    : `${base} text-slate-700 border-slate-800 bg-slate-900/30`;

  return (
    <div className={cls}>
      {state.status === 'running'
        ? <Loader2 size={13} className="animate-spin" />
        : state.status === 'done'
        ? <CheckCircle size={13} />
        : <div className="w-3 h-3 rounded-full bg-slate-800 border border-slate-700" />}
      {meta.label}
    </div>
  );
}

// ── MAIN ─────────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus>('idle');
  const [pipeline, setPipeline] = useState<PipelineState>(EMPTY_PIPELINE);
  const [file, setFile] = useState<File | null>(null);

  // Local Jobs
  const [localJobs, setLocalJobs] = useState<any[]>([]);
  const [searchLinks, setSearchLinks] = useState<any>(null);
  const [localJobsLoading, setLocalJobsLoading] = useState(false);

  // Interactive Interview
  const [interviewQAs, setInterviewQAs] = useState<InterviewQA[]>([]);
  const [currentAnswerIdx, setCurrentAnswerIdx] = useState(0);
  const [draftAnswer, setDraftAnswer] = useState('');
  const [interviewDone, setInterviewDone] = useState(false);

  // Job Apply Tracker
  const [jobTracker, setJobTracker] = useState<Record<string, JobTrack>>({});

  // Cover Letter
  const [coverModal, setCoverModal] = useState<CoverLetter | null>(null);
  const [copiedLetter, setCopiedLetter] = useState(false);

  // ATS Score
  const [atsScore, setAtsScore] = useState<ATSScore | null>(null);
  const [atsLoading, setAtsLoading] = useState(false);

  // PDF Report
  const [pdfLoading, setPdfLoading] = useState(false);

  const cancelRef = useRef(false);

  const navItems = [
    { id: 'overview',  label: 'Overview',    icon: <Brain size={15} /> },
    { id: 'matches',   label: 'Job Matches', icon: <TrendingUp size={15} /> },
    { id: 'local',     label: 'Local Jobs 🇮🇳', icon: <Globe size={15} /> },
    { id: 'tracker',   label: 'Tracker',    icon: <CheckSquare size={15} /> },
    { id: 'skills',    label: 'Skill Gap',  icon: <Target size={15} /> },
    { id: 'interview', label: 'AI Interview', icon: <Mic size={15} /> },
    { id: 'letters',   label: 'Cover Letter', icon: <PenLine size={15} /> },
  ];

  // ── Persistence: load on mount ──────────────────────────────────────────
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const { pipeline: p, localJobs: lj, searchLinks: sl } = JSON.parse(saved);
        if (p) { setPipeline(p); setPipelineStatus('done'); }
        if (lj) setLocalJobs(lj);
        if (sl) setSearchLinks(sl);
      }
      const tracker = localStorage.getItem(TRACKER_KEY);
      if (tracker) setJobTracker(JSON.parse(tracker));
    } catch {}
  }, []);

  // ── Persistence: save on change ──────────────────────────────────────────
  useEffect(() => {
    if (pipelineStatus === 'done') {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ pipeline, localJobs, searchLinks }));
      } catch {}
    }
  }, [pipelineStatus, pipeline, localJobs, searchLinks]);

  useEffect(() => {
    try { localStorage.setItem(TRACKER_KEY, JSON.stringify(jobTracker)); } catch {}
  }, [jobTracker]);

  // ── Derived state ────────────────────────────────────────────────────────
  const resumeData   = pipeline.resume.data;
  const skills: string[]     = resumeData?.knowledge_graph?.skills || [];
  const experiences: string[] = resumeData?.knowledge_graph?.experiences || [];
  const jobMatches   = pipeline.matching.data?.job_matches || [];
  const gapData      = pipeline.gaps.data;
  const interviewData = pipeline.interview.data;
  const careerData   = pipeline.career.data;
  const isProcessing = pipelineStatus === 'streaming';
  const isDone       = pipelineStatus === 'done';

  // ── Init interview Q&As when data arrives ───────────────────────────────
  useEffect(() => {
    if (interviewData?.questions && interviewQAs.length === 0) {
      setInterviewQAs(interviewData.questions.map((q: string) => ({
        question: q, answer: '', evaluation: null, evaluating: false
      })));
    }
  }, [interviewData]);

  // ── Fetch local jobs ─────────────────────────────────────────────────────
  const fetchLocalJobs = useCallback(async (sk: string[]) => {
    if (!sk.length) return;
    setLocalJobsLoading(true);
    try {
      const params = new URLSearchParams({ skills: sk.join(','), location: 'india' });
      const res  = await fetch(`http://localhost:8000/local-jobs?${params}`);
      const data = await res.json();
      setLocalJobs(data.jobs || []);
      setSearchLinks(data.search_links || null);
    } catch {} finally { setLocalJobsLoading(false); }
  }, []);

  // ── Generate Cover Letter for a job ──────────────────────────────────────
  const generateCoverLetter = async (job: any, tone: 'professional' | 'friendly' | 'confident' = 'professional') => {
    setCoverModal({ job, letter: '', wordCount: 0, loading: true, tone });
    try {
      const res = await fetch('http://localhost:8000/cover-letter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_title: job.title,
          company: job.company,
          job_description: job.description || '',
          candidate_skills: skills,
          candidate_experiences: experiences,
          candidate_summary: resumeData?.knowledge_graph?.preview || '',
          tone
        })
      });
      const data = await res.json();
      setCoverModal({ job, letter: data.cover_letter, wordCount: data.word_count, loading: false, tone });
    } catch (e) {
      setCoverModal(prev => prev ? { ...prev, loading: false, letter: 'Error generating letter. Please try again.' } : null);
    }
  };

  // ── Fetch ATS score once analysis is done ────────────────────────────────
  const fetchATSScore = useCallback(async (sk: string[], exp: string[], topJob: string) => {
    setAtsLoading(true);
    try {
      const res = await fetch('http://localhost:8000/resume-score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skills: sk, experiences: exp, job_title: topJob })
      });
      const data = await res.json();
      setAtsScore(data);
    } catch {} finally { setAtsLoading(false); }
  }, []);

  // ── Submit answer for evaluation ─────────────────────────────────────────
  const submitAnswer = async (idx: number) => {
    const qa = interviewQAs[idx];
    if (!qa.answer.trim()) return;
    setInterviewQAs(prev => prev.map((q, i) => i === idx ? { ...q, evaluating: true } : q));
    try {
      const res = await fetch('http://localhost:8000/interview/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: qa.question, answer: qa.answer,
          role: interviewData?.role || 'ML Engineer', skills
        })
      });
      const ev = await res.json();
      setInterviewQAs(prev => prev.map((q, i) => i === idx ? { ...q, evaluation: ev, evaluating: false } : q));
      if (idx === interviewQAs.length - 1) setInterviewDone(true);
      else setCurrentAnswerIdx(idx + 1);
    } catch {
      setInterviewQAs(prev => prev.map((q, i) => i === idx ? { ...q, evaluating: false } : q));
    }
  };

  // ── SSE Pipeline ─────────────────────────────────────────────────────────
  const handleAnalyze = async () => {
    if (!file) return;
    setPipeline(EMPTY_PIPELINE);
    setPipelineStatus('streaming');
    setInterviewQAs([]);
    setInterviewDone(false);
    setCurrentAnswerIdx(0);
    cancelRef.current = false;

    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('http://localhost:8000/analyze-career-stream', {
      method: 'POST', body: formData
    });
    if (!response.ok || !response.body) { setPipelineStatus('error'); return; }

    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    try {
      while (!cancelRef.current) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split('\n')) {
          if (!line.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.agent === 'complete') { setPipelineStatus('done'); break; }
            setPipeline(prev => ({ ...prev, [event.agent]: { status: event.status, data: event.data } }));
            if (event.agent === 'resume' && event.status === 'done') {
              const sk: string[] = event.data?.knowledge_graph?.skills || [];
              if (sk.length) fetchLocalJobs(sk);
            }
            if (event.agent === 'matching' && event.status === 'done') {
              const matches = event.data?.job_matches || [];
              const topJob  = matches[0]?.title || 'ML Engineer';
              const sk: string[]  = pipeline.resume.data?.knowledge_graph?.skills || [];
              const exp: string[] = pipeline.resume.data?.knowledge_graph?.experiences || [];
              if (sk.length) fetchATSScore(sk, exp, topJob);
            }
          } catch {}
        }
      }
    } catch { setPipelineStatus('error'); }
    finally { reader.releaseLock(); if (pipelineStatus !== 'done') setPipelineStatus('done'); }
  };

  const clearHistory = () => {
    localStorage.removeItem(STORAGE_KEY);
    setPipeline(EMPTY_PIPELINE);
    setPipelineStatus('idle');
    setLocalJobs([]);
    setSearchLinks(null);
    setInterviewQAs([]);
    setFile(null);
  };

  // ── Job Tracker helpers ───────────────────────────────────────────────────
  const setJobStatus = (jobKey: string, status: JobStatus) => {
    setJobTracker(prev => ({ ...prev, [jobKey]: { ...prev[jobKey], status, note: prev[jobKey]?.note || '' } }));
  };

  // ── Download PDF Report ───────────────────────────────────────────────────
  const downloadReport = async () => {
    setPdfLoading(true);
    try {
      const payload = {
        skills,
        experiences,
        summary: resumeData?.knowledge_graph?.preview || '',
        job_matches: jobMatches,
        gap_data: gapData || {},
        interview_data: interviewData || {},
        career_data: careerData || {},
        ats_score: atsScore || {},
        candidate_name: 'Candidate',
      };
      const res = await fetch('http://localhost:8000/report/pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('PDF generation failed');
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href     = url;
      a.download = 'JobMatch_AI_Report.pdf';
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('PDF generation failed. Make sure the backend is running.');
    } finally {
      setPdfLoading(false);
    }
  };

  // ── Job Card (shared) ─────────────────────────────────────────────────────
  const JobCard = ({ job, idx, borderColor = 'hover:border-blue-500/30' }: any) => {
    const key = `${job.company}-${job.title}`;
    const track = jobTracker[key];
    return (
      <div className={`bg-slate-900/50 border border-white/5 rounded-3xl p-6 ${borderColor} transition-all group hover:-translate-y-1 flex flex-col justify-between relative overflow-hidden`}>
        <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-blue-600/4 blur-2xl" />
        <div>
          <div className="flex justify-between items-start mb-4">
            <div className="w-11 h-11 bg-white/5 rounded-2xl flex items-center justify-center font-black text-slate-300 border border-white/5 text-lg">{job.company?.[0]}</div>
            <div className="text-right">
              <div className="text-2xl font-black text-white">{job.score}</div>
              <div className="text-[9px] uppercase tracking-widest text-slate-500 font-black">Match</div>
            </div>
          </div>
          <h4 className="font-black text-sm mb-1 group-hover:text-blue-400 transition-colors leading-snug">{job.title}</h4>
          <div className="text-slate-400 text-xs mb-1 flex items-center gap-1"><Briefcase size={11}/>{job.company}</div>
          <div className="text-slate-600 text-xs mb-3 flex items-center gap-1"><MapPin size={11}/>{job.location || job.tags?.[0]}</div>
          <div className="flex flex-wrap gap-1 mb-2">
            {job.matched_skills?.slice(0,3).map((s: string) => (
              <span key={s} className="text-[10px] font-bold px-1.5 py-0.5 bg-green-500/10 text-green-400 border border-green-500/20 rounded flex items-center gap-0.5">
                <CheckCircle size={9}/>{s}
              </span>
            ))}
          </div>
        </div>
        <div className="pt-4 border-t border-white/5 mt-2 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-black text-sm">{job.salary}</span>
            <a href={job.apply_link} target="_blank" rel="noreferrer"
              className="flex items-center gap-1 text-xs font-black bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded-lg transition-colors">
              Apply <ExternalLink size={10}/>
            </a>
          </div>
          {/* Tracker pill row */}
          <div className="flex flex-wrap gap-1">
            {JOB_STATUSES.map(s => (
              <button key={s.id} onClick={() => setJobStatus(key, track?.status === s.id ? null : s.id)}
                className={`text-[9px] font-black px-2 py-0.5 rounded transition-all border ${
                  track?.status === s.id
                    ? `${s.color} border-transparent scale-105`
                    : 'border-white/10 text-slate-600 hover:text-slate-400'
                }`}>
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // ── Overall interview score ───────────────────────────────────────────────
  const avgScore = interviewQAs.filter(q => q.evaluation).length
    ? (interviewQAs.filter(q => q.evaluation).reduce((s, q) => s + (q.evaluation?.score || 0), 0) /
       interviewQAs.filter(q => q.evaluation).length).toFixed(1)
    : null;

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#070709] text-slate-100 font-sans">
      {/* Ambient */}
      <div className="fixed top-0 left-0 w-[60%] h-[60%] bg-blue-700/3 blur-[160px] rounded-full pointer-events-none" />
      <div className="fixed bottom-0 right-0 w-[50%] h-[50%] bg-violet-700/3 blur-[130px] rounded-full pointer-events-none" />

      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-white/5 bg-[#070709]/90 backdrop-blur-2xl">
        <div className="max-w-7xl mx-auto px-6 h-18 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-xl shadow-blue-500/20">
              <Zap className="text-white fill-white" size={18} />
            </div>
            <h1 className="text-lg font-black tracking-tight">
              JobMatch <span className="text-blue-500">v2.0</span>
            </h1>
            <span className="text-[9px] font-black uppercase tracking-widest bg-green-500/10 text-green-400 px-2 py-0.5 rounded border border-green-500/20">Live SSE</span>
          </div>

          <nav className="hidden md:flex items-center gap-6">
            {navItems.map(item => (
              <button key={item.id} onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-1.5 text-xs font-bold uppercase tracking-widest transition-all pb-1 ${
                  activeTab === item.id ? 'text-blue-400 border-b-2 border-blue-400' : 'text-slate-500 hover:text-white'
                }`}>
                {item.icon}{item.label}
              </button>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            {isDone && (
              <button onClick={downloadReport} disabled={pdfLoading}
                className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider text-green-400 hover:text-green-300 border border-green-500/20 bg-green-500/5 hover:bg-green-500/10 px-3 py-1.5 rounded-lg transition-all disabled:opacity-50">
                {pdfLoading ? <Loader2 size={11} className="animate-spin"/> : <FileDown size={11}/>}
                {pdfLoading ? 'Generating...' : 'Download PDF'}
              </button>
            )}
            {isDone && (
              <button onClick={clearHistory}
                className="flex items-center gap-1 text-[10px] font-black uppercase tracking-wider text-slate-500 hover:text-red-400 border border-white/5 px-3 py-1.5 rounded-lg transition-colors">
                <Trash2 size={11}/> Clear
              </button>
            )}
            <div className="w-9 h-9 rounded-xl border border-white/10 bg-slate-800 overflow-hidden">
              <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=JobMatch" alt="User" />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 relative">

        {/* Agent Pipeline Tracker */}
        <div className={`mb-8 p-5 border rounded-2xl transition-all ${
          isProcessing ? 'border-blue-500/30 bg-blue-600/5'
          : isDone ? 'border-green-500/20 bg-green-600/4'
          : 'border-white/5 bg-slate-900/20'
        }`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {isProcessing ? <Loader2 size={16} className="animate-spin text-blue-400" />
                : isDone ? <CheckCircle size={16} className="text-green-400" />
                : <Brain size={16} className="text-slate-600" />}
              <span className="font-black text-xs uppercase tracking-widest">
                {isProcessing ? 'Pipeline Streaming Live' : isDone ? '✓ Analysis Complete' : 'Ready — Upload Resume to Start'}
              </span>
            </div>
            {isDone && (
              <span className="text-[9px] font-black text-slate-500 italic flex items-center gap-1">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> Loaded from cache
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(pipeline).map(([id, state]) => <AgentPill key={id} id={id} state={state as AgentState} />)}
          </div>
        </div>

        {/* Page heading */}
        <div className="mb-8">
          <h2 className="text-3xl font-extrabold tracking-tight mb-1">
            {activeTab === 'overview'  && 'Dashboard'}
            {activeTab === 'matches'   && 'Job Matches'}
            {activeTab === 'local'     && 'Local Jobs 🇮🇳'}
            {activeTab === 'tracker'   && 'Application Tracker'}
            {activeTab === 'skills'    && 'Skill Gap Roadmap'}
            {activeTab === 'interview' && 'AI Interview Simulator'}
          </h2>
          <p className="text-slate-500 text-sm">
            {activeTab === 'overview'  && 'Upload your resume — 5 AI agents analyse and stream results in real-time.'}
            {activeTab === 'matches'   && 'Live Adzuna jobs scored by GPT-4o against your extracted skills.'}
            {activeTab === 'local'     && 'Real-time Indian job market + one-click LinkedIn & Naukri search.'}
            {activeTab === 'tracker'   && 'Track every application: Saved → Applied → Interview → Offer.'}
            {activeTab === 'skills'    && 'GPT-4o gap analysis comparing your profile vs matched job requirements.'}
            {activeTab === 'interview' && 'Answer each question — GPT-4o scores and coaches you instantly.'}
          </p>
        </div>

        {/* ══ OVERVIEW ══════════════════════════════════════════════════════════ */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-7">
            
            {/* Upload sidebar */}
            <div className="lg:col-span-1 space-y-5">
              <div className="bg-slate-900/50 border border-white/5 rounded-3xl p-7 backdrop-blur-xl relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-28 h-28 bg-blue-500/4 blur-3xl" />
                <div className="w-12 h-12 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-4 border border-blue-500/20">
                  <Upload className="text-blue-500" size={22} />
                </div>
                <h3 className="font-bold mb-1">Upload Resume</h3>
                <p className="text-slate-500 text-xs mb-5 leading-relaxed">Real PDF parsing + GPT-4o skill extraction + live job matching.</p>
                <label className="block border-2 border-dashed border-white/7 rounded-2xl p-5 text-center cursor-pointer hover:border-blue-500/30 transition-all mb-4">
                  <input type="file" className="hidden" onChange={e => e.target.files?.[0] && setFile(e.target.files[0])} accept=".pdf,.docx,.txt" />
                  {file
                    ? <div className="text-blue-400 font-bold text-xs flex items-center justify-center gap-2"><FileText size={14}/>{file.name}</div>
                    : <div className="text-slate-600 text-xs">Choose PDF / DOCX</div>}
                </label>
                <button onClick={handleAnalyze} disabled={!file || isProcessing}
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 font-bold py-3.5 rounded-xl hover:from-blue-500 hover:to-indigo-500 transition-all disabled:opacity-40 flex items-center justify-center gap-2 shadow-xl shadow-blue-600/20 active:scale-95 text-sm">
                  {isProcessing ? <><Loader2 size={16} className="animate-spin"/>Agents Running...</> : <><Zap size={16}/>Analyze Now</>}
                </button>
              </div>

              {skills.length > 0 && (
                <div className="bg-blue-600/5 border border-blue-500/20 rounded-3xl p-5 animate-in fade-in slide-in-from-bottom-4">
                  <div className="text-[10px] font-black uppercase tracking-widest text-blue-400 mb-3">GPT-4o Extracted Skills</div>
                  <div className="flex flex-wrap gap-1.5">
                    {skills.map(s => <span key={s} className="text-[11px] font-bold px-2 py-0.5 bg-white/5 border border-white/10 text-slate-300 rounded-lg">{s}</span>)}
                  </div>
                </div>
              )}

              {careerData && (
                <div className="bg-gradient-to-br from-violet-600/10 to-pink-600/4 border border-violet-500/20 rounded-3xl p-5 animate-in fade-in">
                  <div className="text-[10px] font-black uppercase tracking-widest text-violet-400 mb-2">Recruiter Verdict</div>
                  <div className="text-xl font-black mb-2">{careerData.recruiter_verdict}</div>
                  <p className="text-xs text-slate-400 leading-relaxed mb-4">{careerData.trajectory}</p>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-white/5 rounded-xl p-3 text-center">
                      <div className="text-[9px] text-slate-500 uppercase font-black mb-1">3-Year</div>
                      <div className="font-black text-xs">{careerData.salary_3yr}</div>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3 text-center">
                      <div className="text-[9px] text-slate-500 uppercase font-black mb-1">5-Year</div>
                      <div className="font-black text-xs">{careerData.salary_5yr}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* PDF Download Card */}
              {isDone && (
                <div className="bg-gradient-to-br from-green-600/10 to-emerald-600/4 border border-green-500/20 rounded-3xl p-5 animate-in fade-in">
                  <div className="text-[10px] font-black uppercase tracking-widest text-green-400 mb-2">📄 Full Analysis Report</div>
                  <p className="text-xs text-slate-400 leading-relaxed mb-4">
                    Download a branded PDF with all job matches, skill gaps, salary predictions, and interview scores.
                  </p>
                  <button onClick={downloadReport} disabled={pdfLoading}
                    className="w-full flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 font-black text-xs rounded-xl transition-all disabled:opacity-50 shadow-lg shadow-green-600/20 active:scale-95">
                    {pdfLoading
                      ? <><Loader2 size={14} className="animate-spin"/>Generating PDF...</>
                      : <><FileDown size={14}/>Download PDF Report</>}
                  </button>
                </div>
              )}
            </div>

            {/* Main */}
            <div className="lg:col-span-3 space-y-7">
              {pipelineStatus === 'idle' && (
                <div className="flex flex-col items-center justify-center h-56 border border-dashed border-white/5 rounded-3xl text-center">
                  <Zap size={36} className="text-slate-800 mb-4" />
                  <div className="text-slate-600 font-bold">Upload a resume to activate the pipeline</div>
                  <div className="text-slate-800 text-xs mt-2">All 5 agents stream results in real-time</div>
                </div>
              )}

              {/* Job Matches */}
              {jobMatches.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-4 px-1">
                    <h3 className="text-xl font-black">Top Matches</h3>
                    <button onClick={() => setActiveTab('matches')} className="text-xs text-blue-400 font-bold flex items-center gap-1 hover:gap-2 transition-all">View All <ChevronRight size={13}/></button>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    {jobMatches.slice(0,4).map((job: any, idx: number) => <JobCard key={idx} job={job} idx={idx} />)}
                  </div>
                </div>
              )}

              {/* Interview Readiness */}
              {interviewData && (
                <div className="p-6 bg-gradient-to-r from-green-600/8 to-transparent border-l-4 border-green-500 rounded-r-3xl flex items-center justify-between animate-in fade-in">
                  <div>
                    <div className="text-xs text-green-400 font-black uppercase tracking-widest mb-1">Interview Readiness</div>
                    <div className="text-3xl font-black mb-1">{avgScore || interviewData.readiness_score} / 10</div>
                    <p className="text-slate-400 text-xs max-w-lg">{interviewData.feedback}</p>
                  </div>
                  <button onClick={() => setActiveTab('interview')}
                    className="px-5 py-2.5 bg-green-600 hover:bg-green-500 font-black text-xs rounded-full flex items-center gap-1 ml-6 whitespace-nowrap transition-all">
                    Start Mock <ChevronRight size={13}/>
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ══ JOB MATCHES ════════════════════════════════════════════════════════ */}
        {activeTab === 'matches' && (
          <div className="animate-in fade-in">
            {jobMatches.length === 0
              ? <div className="flex flex-col items-center h-56 justify-center border border-dashed border-white/5 rounded-3xl text-slate-600">Run analysis first</div>
              : <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                  {jobMatches.map((job: any, idx: number) => <JobCard key={idx} job={job} idx={idx} />)}
                </div>
            }
          </div>
        )}

        {/* ══ LOCAL JOBS ════════════════════════════════════════════════════════ */}
        {activeTab === 'local' && (
          <div className="animate-in fade-in space-y-7">
            {(searchLinks || skills.length > 0) && (
              <div className="p-5 bg-gradient-to-r from-blue-600/8 to-transparent border border-blue-500/20 rounded-3xl">
                <div className="text-xs font-black uppercase tracking-widest text-blue-400 mb-4">🔗 Search Portals — Pre-filled with YOUR skills</div>
                <div className="flex flex-wrap gap-3">
                  {searchLinks?.linkedin && (
                    <a href={searchLinks.linkedin} target="_blank" rel="noreferrer"
                      className="flex items-center gap-2 px-4 py-2 bg-[#0077B5] hover:bg-[#005f94] text-white font-black text-xs rounded-xl transition-all">
                      <svg className="w-3.5 h-3.5 fill-white" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
                      LinkedIn Jobs <ExternalLink size={11}/>
                    </a>
                  )}
                  {searchLinks?.indeed && (
                    <a href={searchLinks.indeed} target="_blank" rel="noreferrer"
                      className="flex items-center gap-2 px-4 py-2 bg-[#2164f3] hover:bg-[#1a52d0] text-white font-black text-xs rounded-xl transition-all">
                      Indeed India <ExternalLink size={11}/>
                    </a>
                  )}
                  {searchLinks?.naukri && (
                    <a href={searchLinks.naukri} target="_blank" rel="noreferrer"
                      className="flex items-center gap-2 px-4 py-2 bg-[#FF7555] hover:bg-[#e55e3e] text-white font-black text-xs rounded-xl transition-all">
                      Naukri.com <ExternalLink size={11}/>
                    </a>
                  )}
                  <a href={`https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(skills.join(' '))}&location=India`}
                    target="_blank" rel="noreferrer"
                    className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 font-black text-xs rounded-xl transition-all">
                    <Globe size={13}/> LinkedIn HR Profiles <ExternalLink size={11}/>
                  </a>
                </div>
                {skills.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    <span className="text-[10px] text-slate-600 font-black uppercase tracking-wider mr-1 self-center">Searching:</span>
                    {skills.slice(0,6).map(s => <span key={s} className="text-[10px] font-bold px-2 py-0.5 bg-white/5 border border-white/10 text-slate-400 rounded-lg">{s}</span>)}
                  </div>
                )}
              </div>
            )}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-black">Indian Opportunities</h3>
                {localJobsLoading && <Loader2 size={18} className="animate-spin text-blue-400" />}
              </div>
              {localJobsLoading
                ? <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">{[1,2,3,4,5,6].map(i => <div key={i} className="h-44 bg-white/3 rounded-3xl animate-pulse border border-white/5" />)}</div>
                : localJobs.length === 0
                ? <div className="flex flex-col items-center h-56 justify-center border border-dashed border-white/5 rounded-3xl text-slate-600">Run analysis first to populate live Indian jobs</div>
                : <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {localJobs.map((job: any, idx: number) => <JobCard key={idx} job={job} idx={idx} borderColor="hover:border-green-500/30" />)}
                  </div>
              }
            </div>
          </div>
        )}

        {/* ══ APPLICATION TRACKER ════════════════════════════════════════════════ */}
        {activeTab === 'tracker' && (
          <div className="animate-in fade-in space-y-7">
            {/* Kanban summary */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {JOB_STATUSES.map(s => {
                const count = Object.values(jobTracker).filter(t => t.status === s.id).length;
                return (
                  <div key={s.id} className="bg-slate-900/50 border border-white/5 rounded-2xl p-4 text-center">
                    <div className="text-2xl font-black mb-1">{count}</div>
                    <div className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 ${s.color} rounded`}>{s.label}</div>
                  </div>
                );
              })}
            </div>

            {/* All tracked jobs */}
            {[...jobMatches, ...localJobs].length === 0
              ? <div className="flex flex-col items-center h-56 justify-center border border-dashed border-white/5 rounded-3xl text-slate-600 text-center">
                  <CheckSquare size={36} className="mb-4 text-slate-800" />
                  <div className="font-bold">Run analysis to start tracking applications</div>
                  <div className="text-xs mt-2">Use the status buttons on each job card to track progress</div>
                </div>
              : <div>
                  <div className="text-xs font-black uppercase tracking-widest text-slate-500 mb-4">All Jobs — Click a Status to Update</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {[...jobMatches, ...localJobs].map((job: any, idx: number) => <JobCard key={idx} job={job} idx={idx} />)}
                  </div>
                </div>
            }
          </div>
        )}

        {/* ══ SKILL GAP ══════════════════════════════════════════════════════════ */}
        {activeTab === 'skills' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-7 animate-in fade-in">
            <div className="lg:col-span-1 border border-red-500/20 bg-red-500/4 rounded-3xl p-7">
              <h3 className="text-lg font-black mb-1">Critical Gaps</h3>
              <p className="text-slate-500 text-xs mb-5">GPT-4o analysis vs your top matched roles.</p>
              {gapData
                ? <div className="space-y-2">
                    {gapData.missing_skills?.map((skill: string, i: number) => (
                      <div key={i} className="flex items-center gap-3 bg-slate-900/60 p-3.5 rounded-xl border border-white/5 hover:border-red-500/30 transition-all group">
                        <div className="w-7 h-7 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center font-black text-xs border border-red-500/20">{i+1}</div>
                        <div>
                          <div className="font-bold text-sm group-hover:text-red-400 transition-colors">{skill}</div>
                          <div className="text-[10px] text-slate-600 font-black uppercase tracking-wider">High market demand</div>
                        </div>
                      </div>
                    ))}
                    {gapData.roadmap && (
                      <div className="mt-4 p-4 bg-amber-500/5 border border-amber-500/20 rounded-xl text-xs text-amber-300 leading-relaxed">
                        💡 {gapData.roadmap}
                      </div>
                    )}
                  </div>
                : <div className="text-slate-700 text-sm">Run analysis to see gaps.</div>
              }
            </div>
            <div className="lg:col-span-2 bg-slate-900/40 border border-white/5 rounded-3xl p-7">
              <div className="flex justify-between items-center mb-5">
                <h3 className="text-lg font-black">8-Week Roadmap</h3>
                <span className="text-[9px] font-black uppercase tracking-widest px-2 py-1 bg-blue-600 text-white rounded-lg">GPT-4o Plan</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { week: 'Weeks 1-2', topic: 'Vector Infrastructure', desc: 'Master Pinecone & semantic search. Build 3 semantic retrieval projects.', color: 'blue' },
                  { week: 'Weeks 3-5', topic: 'Kubernetes & MLOps', desc: 'Deploy and scale LLM APIs via Docker/K8s. CI/CD for ML.', color: 'purple' },
                  { week: 'Weeks 6-8', topic: 'GraphRAG & RLHF', desc: 'Combine Neo4j with LangGraph for relational RAG. Intro to RLHF.', color: 'green' },
                  { week: 'Target',    topic: 'FAANG Ready 🎯', desc: 'Match score increases to 97%+ for top ML Engineering roles.', color: 'amber' },
                ].map(({ week, topic, desc, color }) => (
                  <div key={week} className="p-4 border border-white/5 rounded-2xl bg-white/2 hover:bg-white/4 transition-colors">
                    <div className={`text-${color}-400 text-[10px] font-black uppercase tracking-wider mb-1`}>{week}</div>
                    <div className="font-black text-sm mb-1.5">{topic}</div>
                    <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ══ AI INTERVIEW ════════════════════════════════════════════════════════ */}
        {activeTab === 'interview' && (
          <div className="animate-in fade-in max-w-3xl mx-auto space-y-6">
            {!interviewData
              ? <div className="flex flex-col items-center h-56 justify-center border border-dashed border-white/5 rounded-3xl text-slate-600">Run analysis first to generate interview questions</div>
              : <>
                  {/* Score banner */}
                  <div className="flex items-center gap-5 p-6 bg-gradient-to-r from-green-600/8 to-transparent border border-green-500/20 rounded-3xl">
                    <div className="text-center shrink-0">
                      <div className="text-5xl font-black">{avgScore || interviewData.readiness_score}</div>
                      <div className="text-[10px] text-green-400 font-black uppercase tracking-widest">/10 Score</div>
                    </div>
                    <div>
                      <div className="text-xs text-green-400 font-black uppercase tracking-widest mb-1">
                        Role: {interviewData.role || 'ML Engineer'}
                      </div>
                      <p className="text-sm text-slate-300">{interviewData.feedback}</p>
                      {interviewQAs.some(q => q.evaluation) && (
                        <div className="mt-2 text-xs text-slate-500">
                          {interviewQAs.filter(q => q.evaluation).length}/{interviewQAs.length} questions answered
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Q&A Cards */}
                  {interviewQAs.map((qa, idx) => (
                    <div key={idx} className={`bg-slate-900/60 border rounded-2xl p-6 transition-all ${
                      idx === currentAnswerIdx && !qa.evaluation ? 'border-blue-500/40' : 'border-white/5'
                    }`}>
                      <div className="flex gap-3 mb-4">
                        <div className="w-8 h-8 rounded-full bg-blue-500/10 text-blue-400 font-black text-sm flex items-center justify-center border border-blue-500/20 shrink-0">Q{idx+1}</div>
                        <p className="text-slate-200 font-medium leading-relaxed">{qa.question}</p>
                      </div>

                      {/* Answer input */}
                      {!qa.evaluation && (
                        <div className="ml-11">
                          <textarea
                            rows={3}
                            placeholder="Type your answer here..."
                            value={idx === currentAnswerIdx ? draftAnswer : qa.answer}
                            onChange={e => {
                              if (idx === currentAnswerIdx) setDraftAnswer(e.target.value);
                              setInterviewQAs(prev => prev.map((q, i) => i === idx ? { ...q, answer: e.target.value } : q));
                            }}
                            disabled={idx !== currentAnswerIdx}
                            className="w-full bg-slate-800/50 border border-white/8 rounded-xl p-3 text-sm text-slate-200 placeholder-slate-600 resize-none focus:outline-none focus:border-blue-500/50 transition-colors disabled:opacity-40"
                          />
                          {idx === currentAnswerIdx && (
                            <button
                              onClick={() => submitAnswer(idx)}
                              disabled={!qa.answer.trim() || qa.evaluating}
                              className="mt-2 flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white font-black text-xs rounded-xl transition-all">
                              {qa.evaluating ? <><Loader2 size={13} className="animate-spin"/>Evaluating...</> : <><Send size={13}/>Submit Answer</>}
                            </button>
                          )}
                        </div>
                      )}

                      {/* Evaluation result */}
                      {qa.evaluation && (
                        <div className="ml-11 mt-3 p-4 bg-slate-800/50 border border-white/8 rounded-xl space-y-3 animate-in fade-in slide-in-from-bottom-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="text-xl font-black">{qa.evaluation.score}/10</span>
                              <Stars n={qa.evaluation.stars} />
                            </div>
                            <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded ${
                              qa.evaluation.score >= 8 ? 'bg-green-500/20 text-green-400'
                              : qa.evaluation.score >= 6 ? 'bg-amber-500/20 text-amber-400'
                              : 'bg-red-500/20 text-red-400'
                            }`}>
                              {qa.evaluation.score >= 8 ? 'Excellent' : qa.evaluation.score >= 6 ? 'Good' : 'Needs Work'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-300 leading-relaxed">{qa.evaluation.feedback}</p>
                          <div className="flex items-start gap-2 p-3 bg-amber-500/5 border border-amber-500/20 rounded-xl">
                            <Award size={13} className="text-amber-400 mt-0.5 shrink-0" />
                            <p className="text-xs text-amber-300 leading-relaxed">{qa.evaluation.better_answer_hint}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Final result */}
                  {interviewDone && avgScore && (
                    <div className="p-7 border border-green-500/30 bg-green-600/5 rounded-3xl text-center animate-in fade-in zoom-in-95">
                      <div className="text-4xl font-black mb-2">🎉 {avgScore} / 10</div>
                      <div className="text-green-400 font-black text-sm uppercase tracking-wider mb-3">Interview Complete!</div>
                      <p className="text-slate-400 text-sm">
                        {Number(avgScore) >= 8 ? 'Outstanding performance! You are ready for FAANG-level interviews.' 
                         : Number(avgScore) >= 6 ? 'Good performance. Review the hints above and practice more.'
                         : 'Keep practising. Focus on the improvement hints for each question.'}
                      </p>
                      <button onClick={() => { setInterviewQAs(prev => prev.map(q => ({ ...q, answer: '', evaluation: null, evaluating: false }))); setCurrentAnswerIdx(0); setInterviewDone(false); setDraftAnswer(''); }}
                        className="mt-4 flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 font-black text-xs rounded-full transition-all mx-auto">
                        <RefreshCw size={13}/> Retry Interview
                      </button>
                    </div>
                  )}
                </>
            }
          </div>
        )}

        {/* ══ COVER LETTER TAB ══════════════════════════════════════════════════ */}
        {activeTab === 'letters' && (
          <div className="animate-in fade-in space-y-7">
            <div className="p-5 bg-gradient-to-r from-violet-600/8 to-transparent border border-violet-500/20 rounded-3xl">
              <div className="text-xs font-black uppercase tracking-widest text-violet-400 mb-2">✍️ GPT-4o Cover Letter Generator</div>
              <p className="text-slate-400 text-sm">Click "Write Letter" on any job below. GPT-4o tailors a cover letter using YOUR extracted skills and experience.</p>
            </div>

            {[...jobMatches, ...localJobs].length === 0
              ? <div className="flex flex-col items-center h-56 justify-center border border-dashed border-white/5 rounded-3xl text-slate-600"><PenLine size={36} className="mb-4 text-slate-800" /><div className="font-bold">Run analysis first to generate cover letters</div></div>
              : <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                  {[...jobMatches, ...localJobs].map((job: any, idx: number) => (
                    <div key={idx} className="bg-slate-900/50 border border-white/5 rounded-3xl p-6 hover:border-violet-500/30 transition-all group flex flex-col justify-between">
                      <div>
                        <div className="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center font-black text-slate-300 border border-white/5 mb-4">{job.company?.[0]}</div>
                        <h4 className="font-black text-sm mb-1 group-hover:text-violet-400 transition-colors">{job.title}</h4>
                        <div className="text-slate-500 text-xs mb-4 flex items-center gap-1"><Briefcase size={11}/>{job.company}</div>
                      </div>
                      <div className="space-y-2">
                        {(['professional', 'friendly', 'confident'] as const).map(tone => (
                          <button key={tone} onClick={() => generateCoverLetter(job, tone)}
                            className={`w-full text-xs font-black py-2 rounded-xl transition-all border flex items-center justify-center gap-2 ${
                              tone === 'professional' ? 'border-violet-500/30 bg-violet-600/10 text-violet-400 hover:bg-violet-600/20'
                              : tone === 'friendly'   ? 'border-blue-500/20 bg-blue-600/8 text-blue-400 hover:bg-blue-600/15'
                              : 'border-amber-500/20 bg-amber-600/8 text-amber-400 hover:bg-amber-600/15'
                            }`}>
                            <PenLine size={12}/> {tone.charAt(0).toUpperCase()+tone.slice(1)} Tone
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
            }
          </div>
        )}

      </main>

      {/* ══ COVER LETTER MODAL ════════════════════════════════════════════════ */}
      {coverModal && (
        <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-xl flex items-center justify-center p-4 animate-in fade-in" onClick={() => setCoverModal(null)}>
          <div className="bg-[#0d0f15] border border-white/10 rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl"
            onClick={e => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-white/8">
              <div>
                <div className="text-[10px] font-black uppercase tracking-widest text-violet-400 mb-1">
                  GPT-4o · {coverModal.tone.charAt(0).toUpperCase()+coverModal.tone.slice(1)} Tone
                </div>
                <h3 className="font-black text-base">{coverModal.job.title} — {coverModal.job.company}</h3>
              </div>
              <div className="flex items-center gap-2">
                {!coverModal.loading && coverModal.letter && (
                  <button onClick={() => {
                    navigator.clipboard.writeText(coverModal.letter);
                    setCopiedLetter(true);
                    setTimeout(() => setCopiedLetter(false), 2000);
                  }} className="flex items-center gap-1.5 px-4 py-2 bg-violet-600 hover:bg-violet-500 font-black text-xs rounded-xl transition-all">
                    {copiedLetter ? <><CheckCircle size={13}/>Copied!</> : <><Copy size={13}/>Copy Letter</>}
                  </button>
                )}
                {/* Regenerate per tone */}
                {!coverModal.loading && (
                  <div className="flex gap-1">
                    {(['professional', 'friendly', 'confident'] as const).map(t => (
                      <button key={t} onClick={() => generateCoverLetter(coverModal.job, t)}
                        className={`text-[9px] font-black px-2 py-1 rounded transition-all border ${
                          coverModal.tone === t ? 'border-violet-400 text-violet-400' : 'border-white/10 text-slate-600 hover:text-slate-400'
                        }`}>{t}</button>
                    ))}
                  </div>
                )}
                <button onClick={() => setCoverModal(null)} className="w-8 h-8 flex items-center justify-center rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
                  <X size={15}/>
                </button>
              </div>
            </div>

            {/* Letter body */}
            <div className="flex-1 overflow-y-auto p-7">
              {coverModal.loading
                ? <div className="flex flex-col items-center justify-center h-48 gap-4">
                    <Loader2 size={28} className="animate-spin text-violet-400" />
                    <div className="text-sm text-slate-400 font-bold">GPT-4o is crafting your cover letter...</div>
                    <div className="text-xs text-slate-600">Tailored to your skills and this specific role</div>
                  </div>
                : <div className="whitespace-pre-wrap text-slate-300 text-sm leading-relaxed font-mono">
                    {coverModal.letter}
                  </div>
              }
            </div>

            {/* Footer */}
            {!coverModal.loading && coverModal.wordCount > 0 && (
              <div className="px-7 py-4 border-t border-white/8 flex items-center justify-between">
                <div className="text-xs text-slate-600 font-bold">{coverModal.wordCount} words · GPT-4o generated</div>
                <div className="flex gap-2">
                  <a href={coverModal.job.apply_link} target="_blank" rel="noreferrer"
                    className="flex items-center gap-1 text-xs font-black bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-xl transition-all">
                    Apply with this letter <ExternalLink size={11}/>
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
