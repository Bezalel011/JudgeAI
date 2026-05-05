import { useRef, useState } from "react";
import { Upload, FileText, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { uploadFile, uploadBatch, processDocument } from "@/services/services";

interface Props {
  onProcessed: () => void;
}

interface UploadedFile {
  file: File;
  documentId?: string;
  status: "pending" | "uploading" | "processing" | "success" | "error";
  error?: string;
}

export const UploadSection = ({ onProcessed }: Props) => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const MAX_FILES = 5;

  const handleFiles = (newFiles: FileList | null | undefined) => {
    if (!newFiles) return;

    const validFiles = Array.from(newFiles).filter((f) => {
      if (f.type !== "application/pdf" && !f.name.toLowerCase().endsWith(".pdf")) {
        toast.error(`${f.name} is not a PDF file.`);
        return false;
      }
      return true;
    });

    const totalFiles = files.length + validFiles.length;
    if (totalFiles > MAX_FILES) {
      toast.error(`Maximum ${MAX_FILES} files allowed. You can add ${MAX_FILES - files.length} more.`);
      return;
    }

    const newUploadedFiles: UploadedFile[] = validFiles.map((f) => ({
      file: f,
      status: "pending",
    }));

    setFiles((prev) => [...prev, ...newUploadedFiles]);
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleProcess = async () => {
    if (files.length === 0) {
      toast.error("Select at least one PDF file.");
      return;
    }

    setLoading(true);
    try {
      // Step 1: Upload files
      const filesToUpload = files.map((f) => f.file);
      
      let uploadResults;
      if (filesToUpload.length === 1) {
        // Single file upload
        const result = await uploadFile(filesToUpload[0]);
        uploadResults = {
          documents: [
            {
              document_id: result.document_id,
              filename: result.filename,
            },
          ],
          failed_uploads: [],
        };
      } else {
        // Batch upload
        uploadResults = await uploadBatch(filesToUpload);
      }

      // Update files with document IDs
      const newFiles = [...files];
      uploadResults.documents.forEach((doc, idx) => {
        if (newFiles[idx]) {
          newFiles[idx].documentId = doc.document_id;
          newFiles[idx].status = "processing";
        }
      });

      // Report failed uploads
      if (uploadResults.failed_uploads.length > 0) {
        uploadResults.failed_uploads.forEach((fail) => {
          const idx = newFiles.findIndex((f) => f.file.name === fail.filename);
          if (idx >= 0) {
            newFiles[idx].status = "error";
            newFiles[idx].error = fail.error;
          }
        });
        toast.error(
          `${uploadResults.failed_uploads.length} file(s) failed to upload.`
        );
      }

      setFiles(newFiles);

      // Step 2: Process each document
      for (const file of newFiles) {
        if (file.documentId && file.status === "processing") {
          try {
            const result = await processDocument(file.documentId);
            if (result.success) {
              file.status = "success";
              const count = result.action_count || 0;
              toast.success(
                `${file.file.name}: Extracted ${count} action(s).`
              );
            } else {
              file.status = "error";
              file.error = result.message || "Processing failed";
              toast.error(`${file.file.name}: ${file.error}`);
            }
          } catch (e) {
            file.status = "error";
            file.error = e instanceof Error ? e.message : "Processing failed";
            toast.error(
              `${file.file.name}: ${file.error}`
            );
          }
        }
      }

      setFiles(newFiles);

      // Clear input
      if (inputRef.current) inputRef.current.value = "";

      // Callback after processing
      onProcessed();

      // Show summary
      const successCount = newFiles.filter((f) => f.status === "success").length;
      if (successCount > 0) {
        toast.success(`Successfully processed ${successCount} file(s).`);
      }
    } catch (e) {
      // ✅ FIXED: Clear state on error to prevent corruption
      setFiles([]);
      toast.error(e instanceof Error ? e.message : "Failed to upload files.");
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "success":
        return "text-green-600 dark:text-green-400";
      case "error":
        return "text-red-600 dark:text-red-400";
      case "processing":
      case "uploading":
        return "text-blue-600 dark:text-blue-400";
      default:
        return "text-muted-foreground";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success":
        return "✓";
      case "error":
        return "✕";
      case "processing":
      case "uploading":
        return "⟳";
      default:
        return "○";
    }
  };

  return (
    <Card className="overflow-hidden border-border/60 shadow-[var(--shadow-card)]">
      <div className="border-b border-border/60 bg-muted/30 px-6 py-4">
        <h2 className="text-base font-semibold text-foreground">Upload Judgment</h2>
        <p className="text-sm text-muted-foreground">Upload court judgment PDFs (max {MAX_FILES} files) to extract structured actions.</p>
      </div>
      <div className="p-6">
        <label
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            handleFiles(e.dataTransfer.files);
          }}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
            dragOver
              ? "border-primary bg-accent"
              : "border-border bg-muted/20 hover:bg-muted/40"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            multiple
            className="sr-only"
            onChange={(e) => handleFiles(e.target.files)}
          />
          {files.length === 0 ? (
            <>
              <Upload className="mb-2 h-8 w-8 text-muted-foreground" />
              <p className="text-sm font-medium text-foreground">
                Click or drag PDFs here
              </p>
              <p className="text-xs text-muted-foreground">
                Up to {MAX_FILES} PDF files supported
              </p>
            </>
          ) : (
            <>
              <Upload className="mb-2 h-8 w-8 text-muted-foreground" />
              <p className="text-sm font-medium text-foreground">
                {files.length} file{files.length !== 1 ? "s" : ""} selected
              </p>
              <p className="text-xs text-muted-foreground">
                Drop more files or click to add
              </p>
            </>
          )}
        </label>

        {/* File List */}
        {files.length > 0 && (
          <div className="mt-6 space-y-2">
            <div className="text-sm font-medium text-foreground">Selected Files:</div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {files.map((file, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/20 p-3"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <FileText className="h-4 w-4 flex-shrink-0 text-primary" />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-foreground">
                        {file.file.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {(file.file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    {loading && file.status !== "pending" && (
                      <span className={`text-xs font-medium ${getStatusColor(file.status)}`}>
                        {file.status === "processing" || file.status === "uploading" ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          getStatusIcon(file.status)
                        )}
                      </span>
                    )}
                    {file.error && (
                      <div className="text-xs text-red-600 dark:text-red-400 max-w-xs truncate">
                        {file.error}
                      </div>
                    )}
                    {!loading && (
                      <button
                        onClick={() => removeFile(idx)}
                        className="text-muted-foreground hover:text-foreground transition-colors"
                        title="Remove file"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-5 flex justify-end gap-2">
          {files.length > 0 && !loading && (
            <Button
              onClick={() => setFiles([])}
              variant="outline"
              size="lg"
            >
              Clear All
            </Button>
          )}
          <Button
            onClick={handleProcess}
            disabled={loading || files.length === 0}
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Processing…
              </>
            ) : (
              <>
                Process {files.length > 1 ? `${files.length} Files` : "Judgment"}
              </>
            )}
          </Button>
        </div>
      </div>
    </Card>
  );
};
