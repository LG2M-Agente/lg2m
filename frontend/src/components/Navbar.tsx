"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  GraduationCap,
  LayoutDashboard,
  BookOpen,
  FileSpreadsheet,
  Settings,
  Award
} from "lucide-react";
import { fetchStudentProfile } from "../lib/api";
import { StudentProfile } from "../lib/types";

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const [profile, setProfile] = useState<StudentProfile | null>(null);

  useEffect(() => {
    fetchStudentProfile()
      .then(setProfile)
      .catch((e) => console.error("Falha ao carregar perfil na barra superior", e));
  }, []);

  const navItems = [
    { label: "Dashboard & Heatmap", href: "/", icon: LayoutDashboard },
    { label: "Arena de Questões", href: "/questoes", icon: BookOpen },
    { label: "Simulados", href: "/simulados", icon: FileSpreadsheet },
    { label: "Perfil & Metas", href: "/perfil", icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-emerald-500 to-cyan-400 p-0.5 flex items-center justify-center shadow-lg shadow-emerald-500/10 shrink-0">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <GraduationCap className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
            <div>
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-emerald-400 to-cyan-300">
                Cognitio.ia
              </span>
              <span className="text-xs block text-slate-400 font-medium">
                Agente de apoio para estudo de vestibulares e concursos
              </span>
            </div>
          </Link>
        </div>

        {/* Navigation links */}
        <nav className="hidden md:flex items-center space-x-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? "bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User pill & focus badge */}
        <div className="flex items-center space-x-3">
          <div className="hidden sm:flex items-center bg-slate-800/80 border border-slate-700 rounded-lg p-1.5 text-xs text-slate-300">
            <span className="px-2 py-0.5 bg-blue-600 text-white rounded font-bold uppercase tracking-wider">
              {profile?.certame_foco || "PSC"}
            </span>
            <span className="mx-2 text-slate-400">|</span>
            <span className="text-slate-300 font-medium">{profile?.nome || "Lucas Eduardo"}</span>
          </div>

          <div className="flex items-center bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs px-2.5 py-1.5 rounded-lg font-semibold">
            <Award className="w-4 h-4 mr-1 text-emerald-400" />
            <span>{profile ? `${profile.taxa_acerto_geral}% acertos` : "Carregando..."}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
