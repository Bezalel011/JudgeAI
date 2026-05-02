import { useRef, useState } from "react";
import { Upload, FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { uploadFile } from "@/services/services";

interface Props {
  onProcessed: () => void;
}

export const UploadSection = ({ onProcessed }: Props) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (f: File | null | undefined) => {
    if (!f) return;
    if (f.type !== "application/pdf" && !f.name.toLowerCase().endsWith(".pdf")) {
      toast.error("Please upload a PDF file.");
      return;
    }
    setFile(f);
  };

  const handleProcess = async () => {
    if (!file) {
      toast.error("Select a PDF file first.");
      return;
    }
    setLoading(true);
    try {
      const result = await uploadFile(file);
      const count = Array.isArray(result?.actions) ? result.actions.length : undefined;
      toast.success(count != null ? `Extracted ${count} action(s).` : "Judgment processed.");
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      onProcessed();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to process PDF.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="overflow-hidden border-border/60 shadow-[var(--shadow-card)]">
      <div className="border-b border-border/60 bg-muted/30 px-6 py-4">
        <h2 className="text-base font-semibold text-foreground">Upload Judgment</h2>
        <p className="text-sm text-muted-foreground">Upload a court judgment PDF to extract structured actions.</p>
      </div>
      <div className="p-6">
        <label
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            handleFile(e.dataTransfer.files?.[0]);
          }}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
            dragOver ? "border-primary bg-accent" : "border-border bg-muted/20 hover:bg-muted/40"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            className="sr-only"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
          {file ? (
            <div className="flex items-center gap-3">
              <FileText className="h-8 w-8 text-primary" />
              <div className="text-left">
                <p className="font-medium text-foreground">{file.name}</p>
                <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
          ) : (
            <>
              <Upload className="mb-2 h-8 w-8 text-muted-foreground" />
              <p className="text-sm font-medium text-foreground">Click or drag a PDF here</p>
              <p className="text-xs text-muted-foreground">Only .pdf files are supported</p>
            </>
          )}
        </label>

        <div className="mt-5 flex justify-end">
          <Button onClick={handleProcess} disabled={loading || !file} size="lg">
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Processing…
              </>
            ) : (
              <>Process Judgment</>
            )}
          </Button>
        </div>
      </div>
    </Card>
  );
};
