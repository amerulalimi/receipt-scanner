import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { OpenRouterHealthData } from "@/lib/api/types";

type OpenRouterHealthCardProps = {
  health: OpenRouterHealthData;
};

export function OpenRouterHealthCard({ health }: OpenRouterHealthCardProps) {
  const ok =
    health.configured && health.key_format_valid && health.auth_ok && health.model_ok;

  return (
    <Card className={ok ? "border-primary/30" : "border-destructive/40"}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">OpenRouter Health Check</CardTitle>
        <CardDescription>
          Test API key connection and vision LLM model.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <p className={ok ? "text-foreground" : "text-destructive"}>
          {health.message}
        </p>
        <ul className="space-y-1 text-muted-foreground">
          <li>Configured: {health.configured ? "Yes" : "No"}</li>
          <li>Key format: {health.key_format_valid ? "OK" : "Failed"}</li>
          <li>OpenRouter auth: {health.auth_ok ? "OK" : "Failed"}</li>
          <li>Vision model: {health.model_ok ? "OK" : "Failed"}</li>
          {health.resolved_model ? (
            <li>Active model: {health.resolved_model}</li>
          ) : null}
          {health.http_status ? <li>HTTP: {health.http_status}</li> : null}
        </ul>
        {!ok ? (
          <p className="text-xs text-muted-foreground">
            Get an API key at{" "}
            <a
              href="https://openrouter.ai/keys"
              target="_blank"
              rel="noopener noreferrer"
              className="underline"
            >
              openrouter.ai/keys
            </a>{" "}
            (format <code className="text-xs">sk-or-v1-...</code>), not a URL.
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
