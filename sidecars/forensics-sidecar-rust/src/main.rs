use serde::{Deserialize, Serialize};
use std::io::{self, Read};

const SCHEMA_VERSION: u8 = 1;

#[derive(Debug, Deserialize)]
struct Request {
    command: String,
    request_id: Option<String>,
}

#[derive(Debug, Serialize)]
struct Finding {
    kind: String,
    summary: String,
}

#[derive(Debug, Serialize)]
struct Response {
    schema_version: u8,
    ok: bool,
    findings: Vec<Finding>,
    error: String,
}

fn main() {
    let mut input = String::new();
    if let Err(error) = io::stdin().read_to_string(&mut input) {
        print_response(false, vec![], format!("stdin read failed: {error}"));
        return;
    }
    let request: Request = match serde_json::from_str(&input) {
        Ok(value) => value,
        Err(error) => {
            print_response(false, vec![], format!("invalid request json: {error}"));
            return;
        }
    };
    match request.command.as_str() {
        "status" | "version" => print_response(
            true,
            vec![Finding {
                kind: "status".to_string(),
                summary: format!(
                    "Forensics sidecar protocol is reachable. Request id: {}",
                    request.request_id.unwrap_or_default()
                ),
            }],
            String::new(),
        ),
        "pcap_export" => print_response(
            false,
            vec![],
            "pcap_export is intentionally disabled in the scaffold until packet capture, signing, and privacy review are complete.".to_string(),
        ),
        other => print_response(false, vec![], format!("unsupported command: {other}")),
    }
}

fn print_response(ok: bool, findings: Vec<Finding>, error: String) {
    let response = Response {
        schema_version: SCHEMA_VERSION,
        ok,
        findings,
        error,
    };
    println!("{}", serde_json::to_string(&response).unwrap());
}
