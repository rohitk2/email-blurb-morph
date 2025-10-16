import { useState } from "react";
import { Button } from "@/components/ui/button";
import { EmailInput } from "@/components/EmailInput";
import { JsonOutput } from "@/components/JsonOutput";
import { toast } from "@/hooks/use-toast";
import { extractEmailToJson } from "@/components/EmailInput";

const Index = () => {
  const [emailText, setEmailText] = useState("");
  const [jsonOutput, setJsonOutput] = useState<{
    broker_name: string;
    broker_email: string;
    brokerage: string;
    complete_address: string;
  } | null>(null);

  const handleGenerate = async () => {
    if (!emailText.trim()) {
      toast({
        title: "No input provided",
        description: "Please paste an email to extract text from.",
        variant: "destructive",
      });
      return;
    }

    try {
      const result = await extractEmailToJson(emailText);
      setJsonOutput(result);

      toast({
        title: "JSON generated successfully",
        description: "Broker details extracted from your email.",
      });
    } catch (err: any) {
      toast({
        title: "Extraction failed",
        description: err?.message ?? "Backend error",
        variant: "destructive",
      });
    }
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
        </div>
      </main>
    </div>
  );
};

export default Index;
