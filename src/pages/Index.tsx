import { useState } from "react";
import { Button } from "@/components/ui/button";
import { EmailInput } from "@/components/EmailInput";
import { JsonOutput } from "@/components/JsonOutput";
import { toast } from "@/hooks/use-toast";

const Index = () => {
  const [emailText, setEmailText] = useState("");
  const [jsonOutput, setJsonOutput] = useState<{ extracted_text: string } | null>(null);

  const handleGenerate = () => {
    if (!emailText.trim()) {
      toast({
        title: "No input provided",
        description: "Please paste an email to extract text from.",
        variant: "destructive",
      });
      return;
    }

    // Extract first 10 words
    const words = emailText.trim().split(/\s+/);
    const firstTenWords = words.slice(0, 10).join(" ");

    const result = {
      extracted_text: firstTenWords,
    };

    setJsonOutput(result);
    
    toast({
      title: "JSON generated successfully",
      description: "First 10 words extracted from your email.",
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-secondary/20">
      {/* Hero Section */}
      <header className="container mx-auto px-4 pt-16 pb-12">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent animate-in fade-in slide-in-from-top-6 duration-700 delay-100">
            MailMorph.ai
          </h1>
          
          <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto animate-in fade-in slide-in-from-top-8 duration-700 delay-200">
            Transform unstructured emails into structured JSON data
          </p>
          
          <p className="text-base text-muted-foreground max-w-xl mx-auto animate-in fade-in slide-in-from-top-10 duration-700 delay-300">
            Paste any email and instantly extract structured information. 
            The future of email parsing, powered by AI.
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 pb-24">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Input Section */}
          <div className="bg-card rounded-2xl p-8 shadow-[var(--shadow-card)] border border-border animate-in fade-in slide-in-from-bottom-4 duration-700 delay-400">
            <EmailInput value={emailText} onChange={setEmailText} />
            
            <Button
              onClick={handleGenerate}
              disabled={!emailText.trim()}
              size="lg"
              className="w-full mt-6 bg-gradient-to-r from-primary to-accent hover:shadow-[var(--shadow-glow)] transition-all duration-300 text-base font-semibold"
            >
              Generate JSON
            </Button>
          </div>

          {/* Output Section */}
          {jsonOutput && <JsonOutput data={jsonOutput} />}

          {/* Future Features Hint */}
          <div className="text-center pt-8 animate-in fade-in duration-1000 delay-700">
            <p className="text-sm text-muted-foreground">
              Coming soon: AI-powered semantic extraction with subject intent, tone analysis, and key action detection
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
