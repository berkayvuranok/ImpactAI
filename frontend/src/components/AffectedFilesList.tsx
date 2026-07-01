import type { AffectedFile } from "../api/types";

export function AffectedFilesList({ files }: { files: AffectedFile[] }) {
  if (!files.length) {
    return <p className="font-mono text-sm text-ink-500">No affected files predicted.</p>;
  }

  return (
    <div className="space-y-3">
      {files.map((file, index) => (
        <div
          key={file.file_path}
          className="panel panel-hover flex items-center justify-between gap-4 px-5 py-4"
          style={{ transitionDelay: `${index * 50}ms` }}
        >
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-3">
              <span className="font-mono text-[10px] text-ink-400">
                {String(file.rank).padStart(2, "0")}
              </span>
              <p className="truncate font-mono text-sm text-ink-900">{file.file_path}</p>
            </div>
          </div>
          <div className="shrink-0 text-right">
            <p className="font-heading text-xl font-bold text-ink-900">
              {(file.break_probability * 100).toFixed(0)}%
            </p>
            <p className="font-mono text-[10px] uppercase tracking-wider text-ink-500">
              imp {(file.node_importance * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
