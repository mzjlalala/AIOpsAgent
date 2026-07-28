/** Markdown 渲染（结论气泡）。 */
import DOMPurify from "dompurify";
import { marked } from "marked";

marked.setOptions({
  gfm: true,
  breaks: true,
});

export function renderMarkdown(source: string): string {
  const raw = marked.parse(source || "", { async: false }) as string;
  return DOMPurify.sanitize(raw);
}
