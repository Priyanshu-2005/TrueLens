import { useCallback, useEffect, useRef, useState } from "react";
import {
  ImageIcon,
  Link2,
  Upload,
  X,
  ClipboardPaste,
  FileImage,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Badge } from "~/components/ui/badge";
import { Separator } from "~/components/ui/separator";
import { cn } from "~/lib/utils";

type UploadTab = "file" | "url";

interface PreviewFile {
  src: string;
  name: string;
  size?: number;
}

export default function UploadMedia() {
  const [activeTab, setActiveTab] = useState<UploadTab>("file");
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState<PreviewFile | null>(null);
  const [urlInput, setUrlInput] = useState("");
  const [urlError, setUrlError] = useState("");
  const [pasteHint, setPasteHint] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith("image/") && !file.type.startsWith("video/"))
      return;
    const src = URL.createObjectURL(file);
    setPreview({ src, name: file.name, size: file.size });
  }, []);

  // Ctrl+V paste support
  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      for (const item of Array.from(items)) {
        if (item.type.startsWith("image/")) {
          const file = item.getAsFile();
          if (file) {
            handleFile(file);
            setActiveTab("file");
            setPasteHint(true);
            setTimeout(() => setPasteHint(false), 2000);
          }
        }
      }
    };
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  }, [handleFile]);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => setIsDragging(false);

  const handleUrlSubmit = () => {
    setUrlError("");
    try {
      const url = new URL(urlInput);
      if (!url.protocol.startsWith("http")) throw new Error();
      setPreview({
        src: urlInput,
        name: urlInput.split("/").pop() || "image",
        size: undefined,
      });
    } catch {
      setUrlError("Please enter a valid image URL.");
    }
  };

  const clearPreview = () => {
    setPreview(null);
    setUrlInput("");
    setUrlError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <main className="flex min-h-[calc(100vh-var(--header-height,4rem))] w-full flex-col items-center justify-center px-6 py-16">
      <div className="w-full max-w-5xl">
        {/* Page header */}
        <div className="mb-10 flex flex-col items-start gap-2">
          <Badge
            variant="outline"
            color="primary"
            className="bg-purple-50 font-mono text-xs tracking-widest text-purple-700 uppercase dark:bg-purple-950 dark:text-purple-300"
          >
            Media Analysis
          </Badge>
          <h1 className="font-geist text-primary text-4xl font-semibold sm:text-4xl">
            Upload Media
          </h1>
          <p className="text-muted-foreground font-space-grotesk text-base sm:text-lg">
            Submit an image or video for AI-powered deepfake and authenticity
            analysis.
          </p>
        </div>

        {/* Main card */}
        <div className="border-border bg-muted/20 grid grid-cols-1 overflow-hidden rounded-2xl border md:grid-cols-2">
          {/* ----------------- LEFT Upload Panel ----------------- */}
          <div className="border-border border-b p-6 md:border-r md:border-b-0 md:p-8">
            {/* Tab switcher */}
            <div className="mb-6 flex gap-1 rounded-lg border p-1">
              <button
                onClick={() => setActiveTab("file")}
                className={cn(
                  "flex flex-1 items-center cursor-pointer justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-all",
                  activeTab === "file"
                    ? "bg-background text-primary shadow-sm"
                    : "text-muted-foreground hover:text-primary",
                )}
              >
                <FileImage className="h-4 w-4" />
                File Upload
              </button>
              <button
                onClick={() => setActiveTab("url")}
                className={cn(
                  "flex flex-1 items-center cursor-pointer justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-all",
                  activeTab === "url"
                    ? "bg-background text-primary shadow-sm"
                    : "text-muted-foreground hover:text-primary",
                )}
              >
                <Link2 className="h-4 w-4" />
                Image URL
              </button>
            </div>

            {activeTab === "file" ? (
              <>
                {/* Drop zone */}
                <div
                  ref={dropZoneRef}
                  onDrop={onDrop}
                  onDragOver={onDragOver}
                  onDragLeave={onDragLeave}
                  onClick={() => !preview && fileInputRef.current?.click()}
                  className={cn(
                    "relative flex min-h-56 cursor-pointer flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed transition-all duration-200",
                    isDragging
                      ? "border-primary bg-primary/5 scale-[1.01]"
                      : preview
                        ? "border-border cursor-default"
                        : "border-border hover:border-primary/60 hover:bg-muted/40",
                  )}
                >
                  {preview ? (
                    <>
                      <img
                        src={preview.src}
                        alt="Preview"
                        className="h-full max-h-52 w-full rounded-lg object-contain"
                        onError={() => setPreview(null)}
                      />
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          clearPreview();
                        }}
                        className="bg-background border-border absolute top-2 right-2 cursor-pointer rounded-full border p-1 shadow-sm transition-opacity hover:opacity-80"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </>
                  ) : (
                    <>
                      <div className="bg-muted rounded-full p-4">
                        <Upload className="text-muted-foreground h-7 w-7" />
                      </div>
                      <div className="text-center">
                        <p className="font-geist text-primary text-sm font-medium">
                          Drop file here or{" "}
                          <span className="text-primary underline underline-offset-2">
                            browse
                          </span>
                        </p>
                        <p className="text-muted-foreground mt-1 text-xs">
                          PNG, JPG, WEBP, MP4 — up to 50MB
                        </p>
                      </div>
                    </>
                  )}
                </div>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,video/*"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleFile(file);
                  }}
                />

                {/* Paste hint */}
                <div
                  className={cn(
                    "mt-4 flex items-center gap-2 rounded-lg border px-3 py-2 text-xs transition-all duration-300",
                    pasteHint
                      ? "border-primary/40 bg-primary/5 text-primary"
                      : "border-border text-muted-foreground",
                  )}
                >
                  <ClipboardPaste className="h-3.5 w-3.5 shrink-0" />
                  <span>
                    {pasteHint
                      ? "✓ Image pasted from clipboard!"
                      : "Press Ctrl+V to paste an image from your clipboard"}
                  </span>
                </div>

                {/* File info */}
                {preview?.size !== undefined && (
                  <div className="border-border bg-muted/30 mt-3 flex items-center justify-between rounded-lg border px-3 py-2 text-xs">
                    <span className="text-muted-foreground max-w-[70%] truncate font-mono">
                      {preview.name}
                    </span>
                    <Badge variant="secondary" className="font-mono text-xs">
                      {formatBytes(preview.size)}
                    </Badge>
                  </div>
                )}
              </>
            ) : (
              /* URL tab */
              <div className="flex flex-col gap-4">
                <div className="bg-muted/40 border-border flex min-h-56 flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed p-6">
                  {preview ? (
                    <div className="relative w-full">
                      <img
                        src={preview.src}
                        alt="URL preview"
                        className="max-h-44 w-full rounded-lg object-contain"
                        onError={() => {
                          setPreview(null);
                          setUrlError("Could not load image from this URL.");
                        }}
                      />
                      <button
                        onClick={clearPreview}
                        className="bg-background border-border absolute top-0 right-0 rounded-full border p-1 shadow-sm hover:opacity-80"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="bg-muted rounded-full p-4">
                        <Link2 className="text-muted-foreground h-7 w-7" />
                      </div>
                      <p className="text-muted-foreground text-center text-sm">
                        Enter an image URL below to load it for analysis
                      </p>
                    </>
                  )}
                </div>

                <div className="flex gap-2">
                  <Input
                    placeholder="https://example.com/image.jpg"
                    value={urlInput}
                    onChange={(e) => {
                      setUrlInput(e.target.value);
                      setUrlError("");
                    }}
                    onKeyDown={(e) => e.key === "Enter" && handleUrlSubmit()}
                    className={cn(
                      "font-mono text-sm",
                      urlError &&
                        "border-destructive focus-visible:ring-destructive",
                    )}
                  />
                  <Button
                    variant="outline"
                    onClick={handleUrlSubmit}
                    className="shrink-0"
                  >
                    Load
                  </Button>
                </div>

                {urlError && (
                  <p className="text-destructive text-xs">{urlError}</p>
                )}
              </div>
            )}
          </div>

          {/* ----------------- RIGHT Upload Panel ----------------- */}
          <div className="flex flex-col justify-between p-6 md:p-8">
            <div className="flex flex-col gap-6">
              <div>
                <h2 className="font-geist text-primary text-2xl font-semibold sm:text-3xl">
                  Upload Media
                </h2>
                <p className="text-muted-foreground font-space-grotesk mt-2 text-sm leading-relaxed sm:text-base">
                  Upload any image or video and our AI will analyze it for signs
                  of manipulation, synthetic generation, or deepfake artifacts —
                  in seconds.
                </p>
              </div>

              <Separator />

              <div className="flex flex-col gap-4">
                <Feature
                  icon={<Zap className="h-4 w-4" />}
                  title="Real-Time Analysis"
                  description="Results in under 5 seconds using on-device and cloud AI inference."
                />
                <Feature
                  icon={<ShieldCheck className="h-4 w-4" />}
                  title="Deepfake Detection"
                  description="Detects facial artifacts, GAN-generated imagery, and frame-level inconsistencies."
                />
                <Feature
                  icon={<ImageIcon className="h-4 w-4" />}
                  title="Multi-format Support"
                  description="Works with JPEG, PNG, WEBP images and MP4 / MOV video files."
                />
              </div>

              <Separator />
            </div>

            <div className="mt-8 flex flex-col gap-3">
              <Button
                size="lg"
                disabled={!preview}
                className="font-space-grotesk w-full cursor-pointer text-base shadow-none"
              >
                <ShieldCheck strokeWidth={2.5} />
                Analyze Media
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={clearPreview}
                disabled={!preview}
                className="bg-muted/50 font-space-grotesk w-full cursor-pointer text-base shadow-none"
              >
                <X strokeWidth={2} />
                Clear
              </Button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

function Feature({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="bg-muted border-border mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md border">
        <span className="text-primary">{icon}</span>
      </div>
      <div>
        <p className="font-geist text-primary text-sm font-medium">{title}</p>
        <p className="text-muted-foreground mt-0.5 text-xs leading-relaxed">
          {description}
        </p>
      </div>
    </div>
  );
}
