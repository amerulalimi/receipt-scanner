import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  Briefcase,
  Building2,
  Camera,
  CheckCircle,
  Crown,
  HelpCircle,
  LayoutDashboard,
  Package,
  Receipt,
  Sparkles,
  TrendingUp,
  User,
} from "lucide-react";

export const NAV_LINKS = [
  { label: "Ciri-ciri", href: "#features" },
  { label: "Untuk Syarikat", href: "#segments" },
  { label: "FAQ", href: "#faq" },
] as const;

export const ROUTES = {
  signup: "/register",
  login: "/login",
  demo: "/demo",
  forBusiness: "/for-business",
  forIndividual: "/register",
} as const;

export const HERO_CONTENT = {
  headline: "Urus Resit. Maksimumkan Pelepasan Cukai. Tanpa Kerumitan.",
  subheadline:
    "Resit.my ialah platform pintar yang membantu individu dan syarikat di Malaysia mengimbas, menyusun, dan menjejak resit tuntutan pelepasan cukai Borang BE — sepanjang tahun, bukan pada saat-saat akhir.",
  primaryCta: "Daftar Sekarang — Percuma",
  secondaryCta: "Lihat Demo",
  trustLine:
    "Disokong oleh AI klasifikasi automatik · Selamat untuk audit LHDN · Simpanan 7 tahun",
} as const;

export type ProblemItem = {
  icon: LucideIcon;
  problem: string;
  impact: string;
};

export const PROBLEM_CONTENT = {
  headline: "Bunyi Macam Familiar?",
  closing: "Resit.my selesaikan semua ini — secara automatik.",
  items: [
    {
      icon: Receipt,
      problem: "Resit hilang atau kusut sepanjang tahun",
      impact: "Kerugian tuntutan pelepasan cukai",
    },
    {
      icon: HelpCircle,
      problem: "Tak pasti kategori tuntutan yang betul",
      impact: "Risiko silap fail atau audit LHDN",
    },
    {
      icon: BarChart3,
      problem: "Tak tahu baki had tuntutan lagi",
      impact: "Terlepas peluang jimat cukai",
    },
    {
      icon: Building2,
      problem: "HR penat semak resit pekerja satu-satu",
      impact: "Proses lambat, banyak human error",
    },
  ] satisfies ProblemItem[],
} as const;

export type HowItWorksStep = {
  step: number;
  title: string;
  description: string;
};

export const HOW_IT_WORKS_CONTENT = {
  headline: "Tiga Langkah Mudah",
  steps: [
    {
      step: 1,
      title: "Scan",
      description:
        "Imbas resit terus dari desktop, atau guna QR code untuk snap dari telefon dalam masa saat.",
    },
    {
      step: 2,
      title: "AI Susun",
      description:
        "Sistem AI kami baca resit dan kategorikannya secara automatik mengikut jenis pelepasan cukai (perubatan, pendidikan, gaya hidup, dan lain-lain).",
    },
    {
      step: 3,
      title: "Jejak & Eksport",
      description:
        "Pantau baki had tuntutan secara masa nyata, dan eksport semua resit dalam satu fail ZIP bila-bila masa untuk fail Borang BE atau tujuan audit.",
    },
  ] satisfies HowItWorksStep[],
} as const;

export type FeatureItem = {
  icon: LucideIcon;
  title: string;
  description: string;
};

export const FEATURES_CONTENT = {
  headline: "Semua yang Anda Perlukan, Dalam Satu Platform",
  items: [
    {
      icon: Camera,
      title: "Scan & Muat Naik Pintar",
      description:
        "Snap dari telefon melalui QR code atau muat naik terus dari desktop.",
    },
    {
      icon: Sparkles,
      title: "Klasifikasi AI Automatik",
      description:
        "Teknologi OCR + LLM membaca dan mengkategorikan resit dengan tepat.",
    },
    {
      icon: TrendingUp,
      title: "Jejak Had Tuntutan",
      description:
        "Lihat baki tuntutan yang masih ada bagi setiap kategori, mengikut tahun taksiran.",
    },
    {
      icon: LayoutDashboard,
      title: "Dashboard & Laporan",
      description:
        "Ringkasan tuntutan, perbandingan tahun ke tahun, dan skor kelengkapan dokumen.",
    },
    {
      icon: Package,
      title: "Eksport Sedia Audit",
      description:
        "Muat turun semua resit dan ringkasan dalam format ZIP, disimpan sehingga 7 tahun.",
    },
    {
      icon: CheckCircle,
      title: "Panduan Ready to File",
      description: "Semakan automatik sebelum anda menghantar Borang BE.",
    },
  ] satisfies FeatureItem[],
} as const;

export type SegmentItem = {
  id: string;
  label: string;
  icon: LucideIcon;
  description: string;
};

export const SEGMENTS_CONTENT = {
  headline: "Direka untuk Setiap Peringkat Pengguna",
  items: [
    {
      id: "individu",
      label: "Individu",
      icon: User,
      description:
        "Urus resit peribadi sepanjang tahun, jejak had tuntutan, dan bersedia untuk musim cukai tanpa tergesa-gesa.",
    },
    {
      id: "pekerja",
      label: "Pekerja Syarikat",
      icon: Briefcase,
      description:
        "Hantar resit tuntutan terus kepada HR — cepat, telus, dan tanpa borang manual.",
    },
    {
      id: "hr",
      label: "HR Admin",
      icon: Building2,
      description:
        "Lulus atau tolak tuntutan pekerja, dapatkan analitik menyeluruh, dan eksport data terus ke sistem penggajian (CSV).",
    },
    {
      id: "superadmin",
      label: "Superadmin Syarikat",
      icon: Crown,
      description:
        "Urus dasar organisasi, akses HR, dan billing syarikat dalam satu dashboard bersepadu.",
    },
  ] satisfies SegmentItem[],
  individualCta: "Untuk Individu →",
  businessCta: "Untuk Syarikat →",
} as const;

export type TrustItem = {
  title: string;
  description: string;
};

export const TRUST_CONTENT = {
  headline: "Dibina Khusus untuk Sistem Cukai Malaysia",
  items: [
    {
      title: "Patuh LHDN",
      description:
        "Kategori pelepasan cukai sentiasa dikemas kini mengikut garis panduan Borang BE terkini.",
    },
    {
      title: "Simpanan 7 Tahun",
      description:
        "Memenuhi keperluan simpanan rekod untuk tujuan audit LHDN.",
    },
    {
      title: "Dwibahasa",
      description: "Sokongan penuh Bahasa Melayu dan Bahasa Inggeris.",
    },
    {
      title: "Keselamatan Data",
      description:
        "Resit dan maklumat peribadi anda disulitkan dan disimpan dengan selamat.",
    },
  ] satisfies TrustItem[],
} as const;

export type FaqItem = {
  question: string;
  answer: string;
};

export const FAQ_CONTENT = {
  headline: "Soalan Lazim",
  items: [
    {
      question: "Adakah Resit.my percuma?",
      answer:
        "Anda boleh mendaftar dan mula guna Resit.my sekarang secara percuma.",
    },
    {
      question: "Adakah data resit saya selamat?",
      answer:
        "Ya. Semua resit dan data disulitkan dan disimpan mengikut standard keselamatan data, dengan tempoh simpanan sehingga 7 tahun untuk tujuan audit.",
    },
    {
      question: "Bolehkah syarikat saya guna Resit.my untuk semua pekerja?",
      answer:
        "Ya, Resit.my menyediakan sistem peranan berbilang peringkat (pekerja, HR Admin, Superadmin) khusus untuk keperluan organisasi.",
    },
    {
      question: "Adakah Resit.my menyokong Bahasa Inggeris?",
      answer:
        "Ya, platform ini tersedia sepenuhnya dalam Bahasa Melayu dan Bahasa Inggeris.",
    },
  ] satisfies FaqItem[],
} as const;

export const CTA_CONTENT = {
  headline: "Bersedia untuk Musim Cukai Tanpa Tergesa-gesa?",
  subtext:
    "Sertai Resit.my hari ini dan mulakan urus resit anda dengan cara yang lebih pintar.",
  button: "Daftar Sekarang — Percuma",
} as const;

export const FOOTER_CONTENT = {
  tagline: "Resit.my — Scanner resit pintar untuk rakyat Malaysia.",
  columns: [
    {
      title: "Produk",
      links: [
        { label: "Ciri-ciri", href: "#features" },
        { label: "Pricing", href: "#" },
        { label: "Untuk Syarikat", href: "#segments" },
      ],
    },
    {
      title: "Syarikat",
      links: [
        { label: "Tentang Kami", href: "#" },
        { label: "Hubungi Kami", href: "#" },
      ],
    },
    {
      title: "Legal",
      links: [
        { label: "Privasi", href: "#" },
        { label: "Terma Penggunaan", href: "#" },
      ],
    },
  ],
  copyright: "© 2026 Resit.my. Hak cipta terpelihara.",
} as const;
