import { Card } from "@/components/ui/card";

interface JsonOutputProps {
  data: { extracted_text: string; word_count?: number; max_words?: number } | null;
}

export const JsonOutput = ({ data }: JsonOutputProps) => {
  if (!data) return null;

  const formattedJson = JSON.stringify(data, null, 2);

  return (
    <div className="space-y-3 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <h3 className="text-lg font-medium">Extracted JSON</h3>
      <Card className="bg-card shadow-[var(--shadow-card)]">
        <pre className="p-6 overflow-x-auto">
          <code className="text-sm font-mono text-foreground">
            {formattedJson}
          </code>
        </pre>
      </Card>
    </div>
  );
};
