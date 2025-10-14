import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

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
