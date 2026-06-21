import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { I18nProvider } from "@/components/providers/i18n-provider";
import { NuqsProvider } from "@/components/providers/nuqs-provider";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { getDictionary, getLocale } from "@/lib/i18n/get-dictionary";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Resit.my",
    template: "%s | Resit.my",
  },
  description:
    "Malaysian tax relief receipt scanner — scan, classify, and manage resit for Borang BE.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getLocale();
  const dictionary = await getDictionary(locale);

  return (
    <html
      lang={locale}
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <I18nProvider locale={locale} dictionary={dictionary}>
          <NuqsProvider>
            <TooltipProvider>
              {children}
              <Toaster />
            </TooltipProvider>
          </NuqsProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
