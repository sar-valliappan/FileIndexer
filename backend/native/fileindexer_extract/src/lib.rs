use pyo3::prelude::*;

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

/// A Python module implemented in Rust.
#[pymodule]
mod fileindexer_extract {
    use super::{extract_pdf, extract_plain};
    use pyo3::prelude::*;

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
}
