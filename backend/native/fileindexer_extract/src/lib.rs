use pyo3::prelude::*;
use quick_xml::events::Event;
use quick_xml::reader::Reader;
use std::io::Read;

fn extract_plain(path: &str) -> Option<String> {
    match std::fs::read(path) {
        Ok(bytes) => Some(String::from_utf8_lossy(&bytes).into_owned()),
        Err(e) => {
            eprintln!("Error extracting text from TXT or MD: {e}");
            None
        }
    }
}

fn extract_pdf(path: &str) -> Option<String> {
    match pdf_extract::extract_text(path) {
        Ok(text) => Some(text),
        Err(e) => {
            eprintln!("Error extracting text from PDF: {e}");
            None
        }
    }
}

/// Strips out all text runs from an XML part of an OOXML document.
fn strip_text_runs(xml: &str) -> String {
    let mut reader = Reader::from_str(xml);
    let mut out = String::new();
    let mut buf = Vec::new();
    let mut in_text = false;
    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                if e.local_name().as_ref() == b"t" {
                    in_text = true;
                }
            }
            Ok(Event::Text(e)) => {
                if in_text {
                    if let Ok(decoded) = e.decode() {
                        out.push_str(&decoded);
                    }
                }
            }
            // Entity/char references (e.g. `&amp;`, `&#8212;`) arrive as their
            // own event rather than inline in Event::Text.
            Ok(Event::GeneralRef(e)) => {
                if in_text {
                    if e.is_char_ref() {
                        if let Ok(Some(c)) = e.resolve_char_ref() {
                            out.push(c);
                        }
                    } else if let Ok(name) = e.decode() {
                        if let Some(resolved) = quick_xml::escape::resolve_predefined_entity(&name) {
                            out.push_str(resolved);
                        }
                    }
                }
            }
            Ok(Event::End(e)) => {
                let local = e.local_name();
                if local.as_ref() == b"t" {
                    in_text = false;
                } else if local.as_ref() == b"p" {
                    out.push('\n');
                }
            }
            // Self-closing elements (e.g. an empty `<w:p/>`) never produce a
            // separate End event, so paragraph breaks must be handled here too.
            Ok(Event::Empty(e)) => {
                if e.local_name().as_ref() == b"p" {
                    out.push('\n');
                }
            }
            Ok(Event::Eof) => break,
            Err(_) => break,
            _ => {}
        }
        buf.clear();
    }
    out
}

/// Reads a single XML part out of a zip (docx/pptx are zipped OOXML) and strips its text runs.
fn extract_ooxml_part(path: &str, entry: &str) -> Option<String> {
    let file = std::fs::File::open(path)
        .map_err(|e| eprintln!("Error opening file: {e}"))
        .ok()?;
    let mut archive = zip::ZipArchive::new(file)
        .map_err(|e| eprintln!("Error reading zip archive: {e}"))
        .ok()?;
    let mut xml = String::new();
    archive
        .by_name(entry)
        .map_err(|e| eprintln!("Error reading {entry}: {e}"))
        .ok()?
        .read_to_string(&mut xml)
        .map_err(|e| eprintln!("Error reading {entry}: {e}"))
        .ok()?;
    Some(strip_text_runs(&xml))
}

fn extract_docx(path: &str) -> Option<String> {
    match extract_ooxml_part(path, "word/document.xml") {
        Some(text) => Some(text),
        None => {
            eprintln!("Error extracting text from DOCX: {path}");
            None
        }
    }
}

// Extension-based dispatch to the appropriate extraction function.
fn process_file_inner(path: &str) -> Option<String> {
    let extension = std::path::Path::new(path)
        .extension()
        .and_then(|e| e.to_str())
        .map(|e| e.to_lowercase());
    match extension.as_deref() {
        Some("pdf") => extract_pdf(path),
        Some("docx") => extract_docx(path),
        Some("txt") | Some("md") => extract_plain(path),
        Some(ext) => {
            println!("Unsupported file type: .{ext}");
            None
        }
        None => {
            println!("Unsupported file type: ");
            None
        }
    }
}

/// A Python module implemented in Rust.
#[pymodule]
mod fileindexer_extract {
    use super::{extract_docx, extract_pdf, extract_plain, process_file_inner};
    use pyo3::prelude::*;
    use rayon::prelude::*;

    /// Extract text from a TXT or MD file (lossy UTF-8 decode).
    #[pyfunction]
    fn extract_text(path: &str) -> PyResult<Option<String>> {
        Ok(extract_plain(path))
    }

    /// Extract text from a PDF file.
    #[pyfunction]
    fn extract_text_from_pdf(path: &str) -> PyResult<Option<String>> {
        Ok(extract_pdf(path))
    }

    /// Extract text from a DOCX file.
    #[pyfunction]
    fn extract_text_from_docx(path: &str) -> PyResult<Option<String>> {
        Ok(extract_docx(path))
    }

    /// Process a file and extract its text based on extension (pdf/docx/txt/md).
    #[pyfunction]
    fn process_file(path: &str) -> PyResult<Option<String>> {
        Ok(process_file_inner(path))
    }

    /// Extract text from every path in parallel across CPU cores.
    #[pyfunction]
    fn process_files_parallel(py: Python<'_>, paths: Vec<String>) -> PyResult<Vec<Option<String>>> {
        let results = py.detach(|| {
            paths
                .par_iter()
                .map(|p| process_file_inner(p))
                .collect::<Vec<_>>()
        });
        Ok(results)
    }
}

