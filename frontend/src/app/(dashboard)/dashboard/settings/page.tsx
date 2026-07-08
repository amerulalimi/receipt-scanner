import { DashboardError } from "@/components/dashboard/dashboard-error";
import { EmailVerificationBanner } from "@/components/dashboard/email-verification-banner";
import { ForwardingEmailCard } from "@/components/settings/forwarding-email-card";
import { NotificationPreferencesForm } from "@/components/settings/notification-preferences-form";
import { SettingsProfileForm } from "@/components/settings/settings-profile-form";
import { SessionsList } from "@/components/settings/sessions-list";
import { fetchSessionsWithFastApi } from "@/lib/api/auth";
import { fetchNotificationPreferences } from "@/lib/api/notifications";
import { requireAuth } from "@/lib/auth/require-auth";
import { redirectAfterSessionExpired } from "@/lib/auth/session-expired-redirect";
import { getSessionCookieHeader } from "@/lib/api/session";
import { getDictionary, getLocale } from "@/lib/i18n/get-dictionary";
import { createServerTranslator } from "@/lib/i18n/translate";
import type { ApiErrorResponse } from "@/lib/api/types";

export async function generateMetadata() {
  const dictionary = await getDictionary(await getLocale());
  return {
    title: dictionary.settings.title,
  };
}

function isUnauthorized(
  status: number,
  body: unknown,
): body is ApiErrorResponse {
  return (
    status === 401 ||
    (typeof body === "object" &&
      body !== null &&
      "success" in body &&
      (body as ApiErrorResponse).success === false &&
      (body as ApiErrorResponse).code === "UNAUTHORIZED")
  );
}

export default async function SettingsPage() {
  const locale = await getLocale();
  const dictionary = await getDictionary(locale);
  const t = createServerTranslator(dictionary);
  const user = await requireAuth("/dashboard/settings");

  const cookie = await getSessionCookieHeader();
  if (!cookie) {
    redirectAfterSessionExpired("/dashboard/settings");
  }

  let sessionsResult;
  let preferencesResult;
  try {
    [sessionsResult, preferencesResult] = await Promise.all([
      fetchSessionsWithFastApi(cookie),
      fetchNotificationPreferences(),
    ]);
  } catch {
    return (
      <DashboardError message={t("settings", "sessionsLoadError")} />
    );
  }

  if (isUnauthorized(sessionsResult.response.status, sessionsResult.body)) {
    redirectAfterSessionExpired("/dashboard/settings");
  }

  const sessions =
    sessionsResult.body.success && sessionsResult.response.status < 400
      ? sessionsResult.body.data
      : [];

  const preferences =
    preferencesResult.body.success && preferencesResult.response.status < 400
      ? preferencesResult.body.data
      : {
          email_enabled: true,
          in_app_enabled: true,
          digest_frequency: "monthly" as const,
        };

  return (
    <main className="w-full space-y-6 py-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          {t("settings", "title")}
        </h1>
        <p className="text-sm text-muted-foreground">
          {t("settings", "subtitle")}
        </p>
      </header>

      {!user.email_verified ? <EmailVerificationBanner email={user.email} /> : null}

      <div className="grid gap-6 xl:grid-cols-[1.3fr_1fr]">
        <div className="space-y-6">
          <SettingsProfileForm user={user} />
          <ForwardingEmailCard forwardingToken={user.user_id.slice(0, 8)} />
          <NotificationPreferencesForm preferences={preferences} />
        </div>
        <SessionsList sessions={sessions} />
      </div>
    </main>
  );
}
