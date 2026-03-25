'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import {
  Zap, Upload, Brain, TrendingUp, Mic, PenLine,
  CheckCircle, ArrowRight, Star, Globe, Shield,
  ChevronRight, Briefcase, Target, Award, BarChart2,
  FileText, Sparkles, Clock, Users, Building2
} from 'lucide-react';

// ── Animated counter ──────────────────────────────────────────────────────────
function Counter({ to, suffix = '' }: { to: number; suffix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const observer = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        let start = 0;
        const step = to / 60;
        const timer = setInterval(() => {
          start += step;
          if (start >= to) { setCount(to); clearInterval(timer); }
          else setCount(Math.floor(start));
        }, 20);
      }
    }, { threshold: 0.5 });
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [to]);
  return <div ref={ref}>{count.toLocaleString()}{suffix}</div>;
}

// ── Agent Step ────────────────────────────────────────────────────────────────
function AgentStep({ n, icon, title, desc, color }: any) {
  return (
    <div className="relative group">
      <div className={`absolute -inset-px rounded-3xl bg-gradient-to-b from-${color}-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
      <div className="relative bg-[#0d0f17] border border-white/6 rounded-3xl p-7 h-full hover:border-white/12 transition-all">
        <div className={`w-12 h-12 rounded-2xl bg-${color}-600/15 border border-${color}-500/25 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform`}>
          <span className={`text-${color}-400`}>{icon}</span>
        </div>
        <div className={`text-[10px] font-black uppercase tracking-widest text-${color}-500 mb-2`}>Agent {n}</div>
        <h3 className="font-black text-base mb-2">{title}</h3>
        <p className="text-slate-500 text-sm leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

// ── Feature Pill ──────────────────────────────────────────────────────────────
function FeatureTag({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-2 px-4 py-2 bg-white/4 border border-white/8 rounded-full text-sm font-medium text-slate-300 hover:border-blue-500/30 hover:text-white transition-all cursor-default">
      <span className="text-blue-400">{icon}</span>{text}
    </div>
  );
}

// ── Testimonial Card ──────────────────────────────────────────────────────────
function TestimonialCard({ name, role, company, text, avatar }: any) {
  return (
    <div className="bg-[#0d0f17] border border-white/6 rounded-3xl p-7 hover:border-white/12 transition-all">
      <div className="flex gap-0.5 mb-5">
        {[1,2,3,4,5].map(i => <Star key={i} size={14} className="text-yellow-400 fill-yellow-400" />)}
      </div>
      <p className="text-slate-300 text-sm leading-relaxed mb-6">"{text}"</p>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 to-violet-600 flex items-center justify-center font-black text-sm overflow-hidden">
          <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${avatar}`} alt={name} />
        </div>
        <div>
          <div className="font-black text-sm">{name}</div>
          <div className="text-slate-500 text-xs">{role} · {company}</div>
        </div>
      </div>
    </div>
  );
}

export default function LandingPage() {
  const [uploadHover, setUploadHover] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 60);
    window.addEventListener('scroll', fn);
    return () => window.removeEventListener('scroll', fn);
  }, []);

  const agents = [
    { n: 1, icon: <FileText size={22} />, color: 'blue',   title: 'Resume Intelligence',  desc: 'PyMuPDF parses your PDF. GPT-4o extracts a structured knowledge graph of every skill, project and experience.' },
    { n: 2, icon: <TrendingUp size={22}/>, color: 'violet', title: 'Semantic Job Matching', desc: 'Live Adzuna job listings fetched and scored by GPT-4o against your profile. Sorted by match percentage.' },
    { n: 3, icon: <Target size={22} />,   color: 'amber',  title: 'Skill Gap Analyser',   desc: 'GPT-4o compares your skills vs top matched roles and generates a week-by-week learning roadmap.' },
    { n: 4, icon: <Mic size={22} />,      color: 'green',  title: 'AI Mock Interview',     desc: 'Role-specific questions generated per your resume. Type answers — GPT-4o scores each one instantly.' },
    { n: 5, icon: <Brain size={22} />,    color: 'pink',   title: 'Career War Room',       desc: 'Simulates 3 virtual senior recruiters to predict your 3-year and 5-year salary trajectory.' },
  ];

  const testimonials = [
    { name: 'Arjun Mehta',    role: 'ML Engineer',      company: 'Razorpay',    avatar: 'arjun',   text: 'The cover letter generator alone saved me 3 hours per application. Got 4 interviews in one week.' },
    { name: 'Priya Sharma',   role: 'Data Scientist',   company: 'Freshworks',  avatar: 'priya',   text: 'The AI Interview tab was brutally honest. Fixed my answers before the real interview and got the offer.' },
    { name: 'Rishi Venkat',   role: 'LLM Engineer',     company: 'CRED',        avatar: 'rishi',   text: 'Went from 0 callbacks to 6 in 2 weeks. The skill gap roadmap told me exactly what to learn.' },
  ];

  return (
    <div className="min-h-screen bg-[#07080d] text-slate-100 overflow-hidden">

      {/* Ambient blobs */}
      <div className="fixed top-[-20%] left-[-10%] w-[70%] h-[70%] bg-blue-700/6 blur-[180px] rounded-full pointer-events-none" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-violet-700/6 blur-[160px] rounded-full pointer-events-none" />

      {/* ── NAV ──────────────────────────────────────────────────────────────── */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-[#07080d]/90 backdrop-blur-2xl border-b border-white/5 shadow-2xl' : ''}`}>
        <div className="max-w-7xl mx-auto px-6 h-[70px] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-xl shadow-blue-500/30">
              <Zap className="text-white fill-white" size={18} />
            </div>
            <div>
              <span className="text-lg font-black tracking-tight">JobMatch</span>
              <span className="text-lg font-black text-blue-500"> AI</span>
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest bg-gradient-to-r from-blue-600/20 to-violet-600/20 text-blue-400 px-2 py-0.5 rounded border border-blue-500/20">v2.0</span>
          </div>

          <div className="hidden md:flex items-center gap-8">
            {['How it Works', 'Features', 'Agents', 'Testimonials'].map(item => (
              <a key={item} href={`#${item.toLowerCase().replace(/ /g, '-')}`}
                className="text-sm text-slate-500 hover:text-white transition-colors font-medium">{item}</a>
            ))}
          </div>

          <Link href="/dashboard"
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 font-black text-sm rounded-xl transition-all shadow-lg shadow-blue-600/25 active:scale-95">
            Open Dashboard <ArrowRight size={15}/>
          </Link>
        </div>
      </nav>

      {/* ── HERO ─────────────────────────────────────────────────────────────── */}
      <section className="pt-40 pb-28 px-6 text-center relative">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600/10 border border-blue-500/25 rounded-full text-xs font-black uppercase tracking-widest text-blue-400 mb-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          Live Real-Time · 5 AI Agents · Adzuna API · GPT-4o
        </div>

        {/* Headline */}
        <h1 className="max-w-5xl mx-auto text-5xl md:text-7xl font-black tracking-tight leading-[1.05] mb-7 animate-in fade-in slide-in-from-bottom-6 duration-700 delay-100">
          Your personal{' '}
          <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-violet-500 bg-clip-text text-transparent">
            AI Recruitment
          </span>
          <br />
          command center
        </h1>

        <p className="max-w-2xl mx-auto text-lg text-slate-400 leading-relaxed mb-10 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-200">
          Upload your resume. 5 AI agents stream analysis in real-time — live job matches,
          skill gaps, mock interviews, cover letters, and salary predictions. All powered by GPT-4o.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16 animate-in fade-in slide-in-from-bottom-10 duration-700 delay-300">
          <Link href="/dashboard"
            className="group flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 font-black text-base rounded-2xl transition-all shadow-2xl shadow-blue-600/30 active:scale-95">
            <Zap size={18} className="group-hover:rotate-12 transition-transform fill-white"/>
            Analyse My Resume Free
            <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform"/>
          </Link>
          <a href="#how-it-works"
            className="flex items-center justify-center gap-2 px-8 py-4 bg-white/4 border border-white/10 hover:bg-white/8 font-black text-base rounded-2xl transition-all">
            See How It Works <ArrowRight size={16}/>
          </a>
        </div>

        {/* Feature tags */}
        <div className="flex flex-wrap justify-center gap-2 max-w-3xl mx-auto animate-in fade-in duration-700 delay-500">
          <FeatureTag icon={<Globe size={14}/>}     text="Live Adzuna Jobs" />
          <FeatureTag icon={<Brain size={14}/>}     text="GPT-4o Powered" />
          <FeatureTag icon={<PenLine size={14}/>}   text="Cover Letter Generator" />
          <FeatureTag icon={<Mic size={14}/>}       text="AI Mock Interview" />
          <FeatureTag icon={<Shield size={14}/>}    text="ATS Score Checker" />
          <FeatureTag icon={<TrendingUp size={14}/>} text="Salary Prediction" />
          <FeatureTag icon={<Target size={14}/>}    text="Skill Gap Roadmap" />
          <FeatureTag icon={<CheckCircle size={14}/>} text="Application Tracker" />
        </div>
      </section>

      {/* ── STATS ─────────────────────────────────────────────────────────────── */}
      <section className="py-16 border-y border-white/5">
        <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { to: 5,    suffix: '',    label: 'AI Agents',        icon: <Brain size={20}/> },
            { to: 100,  suffix: '%',   label: 'Real Job Data',    icon: <Globe size={20}/> },
            { to: 8,    suffix: 'k+',  label: 'Adzuna Listings',  icon: <Briefcase size={20}/> },
            { to: 3,    suffix: 's',   label: 'Avg Response Time', icon: <Clock size={20}/> },
          ].map(({ to, suffix, label, icon }) => (
            <div key={label} className="text-center group">
              <div className="flex justify-center text-blue-500 mb-3 group-hover:scale-110 transition-transform">{icon}</div>
              <div className="text-4xl font-black mb-1 bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                <Counter to={to} suffix={suffix} />
              </div>
              <div className="text-slate-500 text-sm font-medium">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── HOW IT WORKS ─────────────────────────────────────────────────────── */}
      <section id="how-it-works" className="py-28 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <div className="text-[10px] font-black uppercase tracking-widest text-blue-400 mb-3">Simple · Fast · Real</div>
            <h2 className="text-4xl font-black mb-4">Get hired in 3 steps</h2>
            <p className="text-slate-500 max-w-xl mx-auto">No sign-up needed. Everything streams live in your browser. Your data never leaves your session.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { step: '01', icon: <Upload size={28}/>, title: 'Upload Resume', desc: 'Drag your PDF or DOCX. We accept any format and parse it using PyMuPDF instantly.', color: 'blue' },
              { step: '02', icon: <Zap size={28}/>,    title: 'Stream Results', desc: 'Watch 5 AI agents run in real-time, each updating the dashboard live as they finish.', color: 'violet' },
              { step: '03', icon: <Award size={28}/>,  title: 'Land the Job',   desc: 'Apply with AI-written cover letters, practise with mock interviews, track all applications.', color: 'green' },
            ].map(({ step, icon, title, desc, color }) => (
              <div key={step} className={`relative bg-[#0d0f17] border border-white/6 rounded-3xl p-8 hover:border-${color}-500/25 transition-all group text-center`}>
                <div className={`absolute -top-4 left-1/2 -translate-x-1/2 text-3xl font-black text-${color}-600/20 select-none`}>{step}</div>
                <div className={`w-14 h-14 mx-auto rounded-2xl bg-${color}-600/12 border border-${color}-500/20 flex items-center justify-center text-${color}-400 mb-5 group-hover:scale-110 group-hover:border-${color}-400/40 transition-all`}>
                  {icon}
                </div>
                <h3 className="font-black text-base mb-2">{title}</h3>
                <p className="text-slate-500 text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 5 AGENTS ─────────────────────────────────────────────────────────── */}
      <section id="agents" className="py-28 px-6 bg-gradient-to-b from-blue-950/5 to-transparent">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="text-[10px] font-black uppercase tracking-widest text-violet-400 mb-3">Real-Time SSE Pipeline</div>
            <h2 className="text-4xl font-black mb-4">5 Specialised AI Agents</h2>
            <p className="text-slate-500 max-w-xl mx-auto">Each agent runs in sequence, passing enriched context to the next. No hallucinations — every output is grounded in your actual resume.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
            {agents.map(a => <AgentStep key={a.n} {...a} />)}
          </div>
        </div>
      </section>

      {/* ── FEATURES GRID ────────────────────────────────────────────────────── */}
      <section id="features" className="py-28 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <div className="text-[10px] font-black uppercase tracking-widest text-green-400 mb-3">Production-Grade</div>
            <h2 className="text-4xl font-black mb-4">Everything you need to get hired</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[
              { icon: <Globe size={22}/>,      color: 'blue',   title: 'Live Job Discovery',        desc: 'Adzuna API fetches real postings the moment your skills are extracted. Always fresh.' },
              { icon: <PenLine size={22}/>,    color: 'violet', title: 'Cover Letter Generator',    desc: '3 tones: Professional, Friendly, Confident. GPT-4o writes the full letter in seconds.' },
              { icon: <Mic size={22}/>,        color: 'green',  title: 'Interactive Mock Interview', desc: 'Type your answers. GPT-4o scores every response 1-10 with ⭐ ratings and coaching.' },
              { icon: <Shield size={22}/>,     color: 'amber',  title: 'ATS Resume Scorer',         desc: 'Know your ATS compatibility before you apply. Get specific improvement suggestions.' },
              { icon: <CheckCircle size={22}/>, color: 'pink',  title: 'Application Tracker',       desc: 'Track every job: Saved → Applied → Interview → Offer. Kanban summary at a glance.' },
              { icon: <BarChart2 size={22}/>,  color: 'cyan',   title: 'Salary Intelligence',       desc: 'GPT-4o predicts your 3-year and 5-year salary trajectory based on your actual profile.' },
              { icon: <Target size={22}/>,     color: 'red',    title: 'Skill Gap Roadmap',         desc: '8-week personalised curriculum. Learn exactly what top matched jobs are requiring.' },
              { icon: <Building2 size={22}/>,  color: 'indigo', title: 'Indian Market Focus 🇮🇳',  desc: 'Naukri, LinkedIn, Indeed India — all pre-filled with your skills for one-click search.' },
              { icon: <Sparkles size={22}/>,   color: 'yellow', title: 'localStorage Persistence',  desc: 'Analysis survives page refresh. Your session is always ready with previous results.' },
            ].map(({ icon, color, title, desc }) => (
              <div key={title} className={`group bg-[#0d0f17] border border-white/6 rounded-3xl p-7 hover:border-${color}-500/20 transition-all`}>
                <div className={`w-11 h-11 rounded-xl bg-${color}-600/10 border border-${color}-500/15 flex items-center justify-center text-${color}-400 mb-4 group-hover:scale-110 transition-transform`}>{icon}</div>
                <h3 className="font-black text-sm mb-1.5">{title}</h3>
                <p className="text-slate-500 text-xs leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ─────────────────────────────────────────────────────── */}
      <section id="testimonials" className="py-28 px-6 bg-gradient-to-b from-violet-950/5 to-transparent">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <div className="text-[10px] font-black uppercase tracking-widest text-yellow-400 mb-3">Real Results</div>
            <h2 className="text-4xl font-black mb-4">Engineers who landed the role</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {testimonials.map(t => <TestimonialCard key={t.name} {...t} />)}
          </div>
        </div>
      </section>

      {/* ── CTA BANNER ───────────────────────────────────────────────────────── */}
      <section className="py-28 px-6">
        <div className="max-w-3xl mx-auto text-center relative">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 via-violet-600/10 to-blue-600/10 rounded-[3rem] blur-3xl" />
          <div className="relative bg-[#0d0f17] border border-white/8 rounded-[2.5rem] p-16">
            <div className="w-16 h-16 mx-auto bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-600/30 mb-7">
              <Zap size={28} className="text-white fill-white" />
            </div>
            <h2 className="text-4xl md:text-5xl font-black mb-4 tracking-tight">Ready to get hired?</h2>
            <p className="text-slate-400 text-lg leading-relaxed mb-10">Upload your resume now. In under 60 seconds, 5 AI agents will show you exactly what to fix, which jobs to apply to, and how much you should earn.</p>
            <Link href="/dashboard"
              className="inline-flex items-center gap-3 px-10 py-5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 font-black text-lg rounded-2xl transition-all shadow-2xl shadow-blue-600/30 active:scale-95 group">
              <Upload size={20}/>
              Upload Resume — It&apos;s Free
              <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform"/>
            </Link>
            <div className="flex items-center justify-center gap-6 mt-8 text-slate-600 text-xs font-bold">
              <span className="flex items-center gap-1"><CheckCircle size={12} className="text-green-600"/> No sign-up required</span>
              <span className="flex items-center gap-1"><CheckCircle size={12} className="text-green-600"/> PDF &amp; DOCX supported</span>
              <span className="flex items-center gap-1"><CheckCircle size={12} className="text-green-600"/> Results in &lt;60 seconds</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────────────────────────── */}
      <footer className="border-t border-white/5 py-10 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
              <Zap size={14} className="text-white fill-white" />
            </div>
            <span className="font-black">JobMatch <span className="text-blue-500">AI</span></span>
            <span className="text-[10px] text-slate-600 font-black uppercase tracking-widest ml-2">v2.0 · Built with GPT-4o + Adzuna</span>
          </div>
          <div className="text-slate-600 text-xs">
            © 2026 JobMatch AI · Real-time agentic recruitment intelligence
          </div>
          <div className="flex items-center gap-4 text-slate-600 text-xs">
            <Link href="/dashboard" className="hover:text-white transition-colors font-bold">Dashboard</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
