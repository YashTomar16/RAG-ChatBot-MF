import { useMemo, type CSSProperties } from "react";

const CELL_SIZE = 44;
const COLS = 34;
const ROWS = 22;

export function ChatBackground() {
  const cells = useMemo(() => {
    const items: Array<{ key: string; diag: number }> = [];
    for (let row = 0; row < ROWS; row += 1) {
      for (let col = 0; col < COLS; col += 1) {
        items.push({ key: `${row}-${col}`, diag: row + col });
      }
    }
    return items;
  }, []);

  return (
    <div className="chat-main-bg" aria-hidden>
      <div className="chat-bg-gradient" />
      <div className="chat-bg-blob chat-bg-blob-1" />
      <div className="chat-bg-blob chat-bg-blob-2" />
      <div className="chat-bg-blob chat-bg-blob-3" />

      <div
        className="chat-bg-grid-cells"
        style={{
          gridTemplateColumns: `repeat(${COLS}, ${CELL_SIZE}px)`,
          gridTemplateRows: `repeat(${ROWS}, ${CELL_SIZE}px)`,
        }}
      >
        {cells.map((cell) => (
          <div
            key={cell.key}
            className="chat-grid-cell"
            style={{ "--diag": cell.diag } as CSSProperties}
          />
        ))}
      </div>

      <div
        className="chat-bg-grid-cells chat-bg-grid-cells-alt"
        style={{
          gridTemplateColumns: `repeat(${COLS}, ${CELL_SIZE}px)`,
          gridTemplateRows: `repeat(${ROWS}, ${CELL_SIZE}px)`,
        }}
      >
        {cells.map((cell) => (
          <div
            key={`alt-${cell.key}`}
            className="chat-grid-cell chat-grid-cell-alt"
            style={{ "--diag": COLS + ROWS - cell.diag } as CSSProperties}
          />
        ))}
      </div>
    </div>
  );
}
