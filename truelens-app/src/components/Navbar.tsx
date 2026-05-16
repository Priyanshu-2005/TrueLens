"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield, Scan, LayoutDashboard, FileCheck, Code2,
  Menu, X, LogIn, ChevronDown
} from "lucide-react";

const navLinks = [
  { href: "/scan", label: "Scan", icon: Scan },
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/documents", label: "Documents", icon: FileCheck },
  { href: "/developers", label: "Developers", icon: Code2 },
];

export default function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border-color"
      style={{ background: "rgba(9, 9, 11, 0.8)", backdropFilter: "blur(16px)" }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="relative">
              <Shield className="w-8 h-8 text-brand-mid transition-colors group-hover:text-brand-light" />
              <div className="absolute inset-0 blur-lg bg-brand-mid/30 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-brand-light to-brand-mid bg-clip-text text-transparent">
              TrueLens
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = pathname === link.href || pathname.startsWith(link.href + "/");
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? "text-brand-light bg-brand-mid/10"
                      : "text-text-muted hover:text-text-primary hover:bg-white/5"
                  }`}
                >
                  <link.icon className="w-4 h-4" />
                  {link.label}
                </Link>
              );
            })}
          </div>

          {/* Right side */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              href="/login"
              className="btn-secondary text-sm !py-2 !px-4"
            >
              <LogIn className="w-4 h-4" />
              <span>Sign In</span>
            </Link>
            <Link
              href="/scan"
              className="btn-primary text-sm !py-2 !px-5"
            >
              <span>Start Scanning</span>
            </Link>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-white/5"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-border-color overflow-hidden"
            style={{ background: "rgba(9, 9, 11, 0.95)" }}
          >
            <div className="px-4 py-4 space-y-1">
              {navLinks.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMobileOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? "text-brand-light bg-brand-mid/10"
                        : "text-text-muted hover:text-text-primary hover:bg-white/5"
                    }`}
                  >
                    <link.icon className="w-5 h-5" />
                    {link.label}
                  </Link>
                );
              })}
              <div className="pt-3 border-t border-border-color mt-3 space-y-2">
                <Link
                  href="/login"
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg text-sm font-medium text-text-muted border border-border-color hover:border-brand-mid"
                >
                  <LogIn className="w-4 h-4" />
                  Sign In
                </Link>
                <Link
                  href="/scan"
                  onClick={() => setMobileOpen(false)}
                  className="btn-primary w-full justify-center text-sm !py-2.5"
                >
                  <span>Start Scanning</span>
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
