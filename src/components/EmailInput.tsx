import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

export async function extractEmailToJson(
  text: string,
  options?: { baseUrl?: string }
): Promise<{
  broker_name: string;
  broker_email: string;
  brokerage: string;
  complete_address: string;
}> {
  const baseUrl = options?.baseUrl ?? "http://localhost:8000";
  const res = await fetch(`${baseUrl}/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
    }),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => "");
    throw new Error(`Extraction failed (${res.status}): ${errText}`);
  }

  return res.json();
}

interface EmailInputProps {
  value: string;
  onChange: (value: string) => void;
}

export const EmailInput = ({ value, onChange }: EmailInputProps) => {
  return (
    <div className="space-y-3">
      <Label htmlFor="email-input" className="text-lg font-medium">
        Paste your email
      </Label>
      <Textarea
        id="email-input"
        placeholder="Paste your email blurb here…"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="min-h-[200px] font-mono text-sm resize-none transition-all duration-300 focus:shadow-lg"
      />
    </div>
  );
};
