"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Toast, ToastType } from "@/components/ui/Toast";
import { Tabs } from "@/components/ui/Tabs";
import {
  BookOpen,
  GraduationCap,
  Sparkles,
  CheckCircle2,
  Clock,
  Award,
  TrendingUp,
  Plus,
  Code,
  Layers,
  FileCode,
  Brain,
  ArrowRight,
  Briefcase,
  HelpCircle,
  BarChart2
} from "lucide-react";

interface SkillItem {
  id: string;
  name: string;
  category: string;
  currentLevel: string;
  targetLevel: string;
  deadline?: string;
  weeklyHours: number;
  progressPercent: number;
  loggedHours: number;
  assessmentScore: number;
  curriculum: any;
}

export default function LearningPage() {
  const [skills, setSkills] = useState<SkillItem[]>([]);
  const [metrics, setMetrics] = useState({
    activeSkillGoals: 0,
    totalStudyHours: 0,
    avgAssessmentScore: 85.0,
    overallProgressPercent: 0.0,
  });

  // AI Recommender Modal
  const [isRecommenderOpen, setIsRecommenderOpen] = useState(false);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [isRecommending, setIsRecommending] = useState(false);

  // New Skill Goal Modal
  const [isNewSkillModalOpen, setIsNewSkillModalOpen] = useState(false);
  const [skillName, setSkillName] = useState("");
  const [currentLevel, setCurrentLevel] = useState("Beginner");
  const [targetLevel, setTargetLevel] = useState("Advanced");
  const [weeklyHours, setWeeklyHours] = useState(5);
  const [isCreatingSkill, setIsCreatingSkill] = useState(false);

  // Log Hours State
  const [selectedSkillForHours, setSelectedSkillForHours] = useState<SkillItem | null>(null);
  const [hoursToLog, setHoursToLog] = useState(1.5);
  const [isLoggingHours, setIsLoggingHours] = useState(false);

  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    fetchLearningDashboard();
  }, []);

  const fetchLearningDashboard = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/learning", {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setSkills(data.skills || []);
        if (data.dashboardMetrics) setMetrics(data.dashboardMetrics);
      }
    } catch (err) {
      console.error("Failed to load learning dashboard", err);
    }
  };

  const handleCreateSkillGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!skillName) return;

    setIsCreatingSkill(true);
    setToast(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/learning/skills", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: skillName,
          currentLevel,
          targetLevel,
          weeklyHours: Number(weeklyHours),
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Skill goal creation failed.");
      }

      const data = await res.json();
      setToast({ type: "success", title: "AI Roadmap Created", message: data.message });
      setIsNewSkillModalOpen(false);
      setSkillName("");
      fetchLearningDashboard();
    } catch (err: any) {
      setToast({ type: "error", title: "Error", message: err.message });
    } finally {
      setIsCreatingSkill(false);
    }
  };

  const handleGetRecommendations = async () => {
    setIsRecommending(true);
    setIsRecommenderOpen(true);

    try {
      const res = await fetch("http://localhost:8000/api/v1/learning/recommend", {
        method: "POST",
        credentials: "include",
      });

      if (res.ok) {
        setRecommendations(await res.json());
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to generate recommendations." });
    } finally {
      setIsRecommending(false);
    }
  };

  const handleLogStudyHours = async () => {
    if (!selectedSkillForHours) return;
    setIsLoggingHours(true);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/learning/${selectedSkillForHours.id}/log-hours`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ hours: Number(hoursToLog) }),
      });

      if (res.ok) {
        setToast({ type: "success", title: "Hours Logged", message: `Added ${hoursToLog}h study time.` });
        setSelectedSkillForHours(null);
        fetchLearningDashboard();
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to log study hours." });
    } finally {
      setIsLoggingHours(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <GraduationCap className="h-6 w-6 text-sky-400" />
            AI Learning Agent & Skill Accelerator
          </h1>
          <p className="text-xs text-muted-foreground">
            Project-connected learning roadmaps, hands-on exercises, mini projects, and skill progress analytics.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="md"
            onClick={handleGetRecommendations}
            leftIcon={<Sparkles className="h-4 w-4 text-purple-400" />}
          >
            What Should I Learn Next?
          </Button>

          <Button
            variant="primary"
            size="md"
            onClick={() => setIsNewSkillModalOpen(true)}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Add Skill Goal
          </Button>
        </div>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* Dashboard Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card glass className="p-4 flex items-center gap-4">
          <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
            <BookOpen className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-muted-foreground block font-mono">Active Skill Goals</span>
            <span className="text-2xl font-bold text-foreground font-mono">{metrics.activeSkillGoals}</span>
          </div>
        </Card>

        <Card glass className="p-4 flex items-center gap-4">
          <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <Clock className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-muted-foreground block font-mono">Total Study Hours</span>
            <span className="text-2xl font-bold text-foreground font-mono">{metrics.totalStudyHours}h</span>
          </div>
        </Card>

        <Card glass className="p-4 flex items-center gap-4">
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Award className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-muted-foreground block font-mono">Avg Assessment Score</span>
            <span className="text-2xl font-bold text-emerald-400 font-mono">{metrics.avgAssessmentScore}%</span>
          </div>
        </Card>

        <Card glass className="p-4 flex items-center gap-4">
          <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <TrendingUp className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-muted-foreground block font-mono">Overall Progress</span>
            <span className="text-2xl font-bold text-indigo-300 font-mono">{metrics.overallProgressPercent}%</span>
          </div>
        </Card>
      </div>

      {/* Skill Roadmaps & Curriculum Cards */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
          <Layers className="h-4 w-4 text-sky-400" />
          Active Skill Roadmaps ({skills.length})
        </h3>

        {skills.map((skill) => (
          <Card key={skill.id} glass className="p-5 space-y-4 hover:border-sky-500/40 transition-all">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/50 pb-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-foreground">{skill.name}</h3>
                  <span className="px-2 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/20 font-mono text-[10px]">
                    {skill.currentLevel} → {skill.targetLevel}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground font-mono">
                  Weekly Budget: {skill.weeklyHours}h/week • Logged: {skill.loggedHours}h
                </span>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-right font-mono">
                  <span className="text-xs text-muted-foreground block">Mastery Score</span>
                  <span className="text-sm font-bold text-emerald-400">{skill.assessmentScore}%</span>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedSkillForHours(skill)}
                  leftIcon={<Clock className="h-3.5 w-3.5 text-purple-400" />}
                >
                  Log Study Hours
                </Button>
              </div>
            </div>

            {/* Progress Meter Bar */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-muted-foreground">Roadmap Completion</span>
                <span className="text-indigo-300 font-bold">{skill.progressPercent}%</span>
              </div>
              <div className="w-full bg-secondary/60 h-2 rounded-full overflow-hidden border border-border/40">
                <div
                  className="bg-gradient-to-r from-sky-500 to-indigo-500 h-full transition-all duration-500"
                  style={{ width: `${skill.progressPercent}%` }}
                />
              </div>
            </div>

            {/* Roadmap Breakdown Tabs / Sections */}
            {skill.curriculum && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                {/* 1. Topics */}
                <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-2 text-xs">
                  <span className="font-bold text-foreground flex items-center gap-1.5 font-mono text-[11px]">
                    <BookOpen className="h-3.5 w-3.5 text-sky-400" /> Topics & Modules
                  </span>
                  <ul className="space-y-1.5 font-mono text-[10px] text-muted-foreground">
                    {skill.curriculum.topics?.map((t: any, idx: number) => (
                      <li key={idx} className="flex items-center justify-between">
                        <span className="truncate">{t.title}</span>
                        <span className="text-emerald-400 font-bold px-1 rounded bg-emerald-500/10">{t.status}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 2. Real Project Connection */}
                <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-2 text-xs">
                  <span className="font-bold text-foreground flex items-center gap-1.5 font-mono text-[11px]">
                    <Briefcase className="h-3.5 w-3.5 text-purple-400" /> Real Project Connection
                  </span>
                  <div className="space-y-1 font-mono text-[10px]">
                    {skill.curriculum.miniProjects?.map((p: any, idx: number) => (
                      <div key={idx} className="p-2 rounded bg-purple-500/10 border border-purple-500/20 text-purple-300">
                        <span className="font-bold block">{p.title}</span>
                        <span className="text-muted-foreground">Connected to: {p.connectedProject}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 3. Exercises & Revision */}
                <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-2 text-xs">
                  <span className="font-bold text-foreground flex items-center gap-1.5 font-mono text-[11px]">
                    <Code className="h-3.5 w-3.5 text-emerald-400" /> Exercises & Revision
                  </span>
                  <ul className="space-y-1.5 font-mono text-[10px] text-muted-foreground">
                    {skill.curriculum.exercises?.map((ex: any, idx: number) => (
                      <li key={idx} className="flex items-center justify-between">
                        <span className="truncate">{ex.title}</span>
                        <span className="text-amber-300 font-bold">{ex.difficulty}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </Card>
        ))}
      </div>

      {/* NEW SKILL GOAL MODAL */}
      <Modal
        isOpen={isNewSkillModalOpen}
        onClose={() => setIsNewSkillModalOpen(false)}
        title="Add New Skill Goal & Generate AI Roadmap"
      >
        <form onSubmit={handleCreateSkillGoal} className="space-y-4 text-xs">
          <div className="space-y-1">
            <label className="font-semibold text-foreground">Skill Name *</label>
            <input
              type="text"
              required
              placeholder="e.g. FastAPI System Architecture & Microservices"
              value={skillName}
              onChange={(e) => setSkillName(e.target.value)}
              className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="font-semibold text-foreground">Current Level</label>
              <select
                value={currentLevel}
                onChange={(e) => setCurrentLevel(e.target.value)}
                className="w-full rounded-xl glass-panel bg-secondary/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 font-mono"
              >
                <option value="Beginner">Beginner</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-foreground">Target Level</label>
              <select
                value={targetLevel}
                onChange={(e) => setTargetLevel(e.target.value)}
                className="w-full rounded-xl glass-panel bg-secondary/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 font-mono"
              >
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced</option>
                <option value="Expert">Expert / Mastery</option>
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label className="font-semibold text-foreground">Weekly Available Study Hours</label>
            <input
              type="number"
              min={1}
              max={40}
              value={weeklyHours}
              onChange={(e) => setWeeklyHours(Number(e.target.value))}
              className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 font-mono"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" type="button" onClick={() => setIsNewSkillModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isCreatingSkill}>
              Generate AI Roadmap
            </Button>
          </div>
        </form>
      </Modal>

      {/* AI SKILL RECOMMENDER MODAL */}
      <Modal
        isOpen={isRecommenderOpen}
        onClose={() => setIsRecommenderOpen(false)}
        title="AI Skill Recommender: What Should I Learn Next?"
      >
        <div className="space-y-4 text-xs">
          {isRecommending ? (
            <div className="p-8 text-center space-y-2 font-mono">
              <Brain className="h-8 w-8 text-purple-400 animate-pulse mx-auto" />
              <p className="text-muted-foreground">Analyzing market demand, client projects, and skill inventory...</p>
            </div>
          ) : (
            recommendations && (
              <div className="space-y-3 font-mono">
                <p className="text-slate-200 text-xs leading-relaxed p-3 rounded-xl bg-purple-950/30 border border-purple-500/30">
                  {recommendations.aiRecommendationsSummary}
                </p>

                <div className="space-y-2">
                  {recommendations.recommendedSkills?.map((rec: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-xl glass-panel bg-secondary/30 border border-border/60 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-foreground">{rec.skill}</span>
                        <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[10px]">
                          {rec.roiCategory}
                        </span>
                      </div>
                      <p className="text-[11px] text-muted-foreground">{rec.reason}</p>
                    </div>
                  ))}
                </div>
              </div>
            )
          )}
        </div>
      </Modal>

      {/* LOG STUDY HOURS MODAL */}
      {selectedSkillForHours && (
        <Modal
          isOpen={!!selectedSkillForHours}
          onClose={() => setSelectedSkillForHours(null)}
          title={`Log Study Hours: ${selectedSkillForHours.name}`}
        >
          <div className="space-y-4 text-xs font-mono">
            <div className="space-y-1">
              <label className="font-semibold text-foreground">Hours Spent Learning</label>
              <input
                type="number"
                step="0.5"
                min="0.5"
                max="12"
                value={hoursToLog}
                onChange={(e) => setHoursToLog(Number(e.target.value))}
                className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setSelectedSkillForHours(null)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleLogStudyHours} isLoading={isLoggingHours}>
                Log Hours
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
