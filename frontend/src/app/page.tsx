import type { Metadata } from "next";

import { HomePageContent } from "@/components/home/home-page";
import { HERO_CONTENT } from "@/components/home/content";

export const metadata: Metadata = {
  title: "Resit.my — Scanner Resit Pintar untuk Pelepasan Cukai Malaysia",
  description: HERO_CONTENT.subheadline,
  openGraph: {
    title: "Resit.my — Scanner Resit Pintar untuk Pelepasan Cukai Malaysia",
    description: HERO_CONTENT.subheadline,
    type: "website",
  },
};

export default function HomePage() {
  return <HomePageContent />;
}
