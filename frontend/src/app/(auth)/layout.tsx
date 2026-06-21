export default function AuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="flex min-h-full flex-1 flex-col items-center justify-center gap-6 bg-muted/30 px-4 py-10">
      <div className="text-center">
        <p className="text-lg font-semibold tracking-tight">Resit.my</p>
        <p className="text-sm text-muted-foreground">
          Malaysian tax receipt scanner
        </p>
      </div>
      {children}
    </div>
  );
}
