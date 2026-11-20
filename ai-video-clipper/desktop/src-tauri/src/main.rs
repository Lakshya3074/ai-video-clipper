use std::env;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::Mutex;
use tauri::{AppHandle, Manager, State};
use tauri_plugin_shell::process::CommandChild;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Clone)]
struct BackendStatus {
    running: bool,
    port: u16,
    url: String,
}

struct BackendState {
    child: Mutex<Option<CommandChild>>,
    port: u16,
}

#[tauri::command]
async fn start_backend(app: AppHandle, state: State<'_, BackendState>) -> Result<BackendStatus, String> {
    let mut child_lock = state.child.lock().unwrap();

    if child_lock.is_some() {
        return Ok(BackendStatus {
            running: true,
            port: state.port,
            url: format!("http://localhost:{}", state.port),
        });
    }

    // Find the sidecar binary
    let resource_dir = app.path().resource_dir().map_err(|e| e.to_string())?;
    let sidecar_path = find_sidecar(&resource_dir)?;

    // Set up environment
    let mut env_vars = env::vars().collect::<std::collections::HashMap<_, _>>();
    env_vars.insert("HOST".to_string(), "127.0.0.1".to_string());
    env_vars.insert("PORT".to_string(), state.port.to_string());
    env_vars.insert("RELOAD".to_string(), "false".to_string());
    env_vars.insert("DATA_DIR".to_string(), get_data_dir()?.to_string_lossy().to_string());

    // Start the sidecar process
    let (mut rx, child) = tauri_plugin_shell::process::Command::new_sidecar("backend")
        .map_err(|e| format!("Failed to create sidecar command: {}", e))?
        .envs(env_vars)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to spawn backend: {}", e))?;

    *child_lock = Some(child);

    // Read stdout/stderr for logging
    let app_handle = app.clone();
    tauri::async_runtime::spawn(async move {
        while let Some(line) = rx.recv().await {
            println!("[Backend] {}", String::from_utf8_lossy(&line));
        }
    });

    // Wait a moment for backend to start
    tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;

    Ok(BackendStatus {
        running: true,
        port: state.port,
        url: format!("http://localhost:{}", state.port),
    })
}

#[tauri::command]
async fn stop_backend(state: State<'_, BackendState>) -> Result<(), String> {
    let mut child_lock = state.child.lock().unwrap();
    if let Some(mut child) = child_lock.take() {
        child.kill().await.map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
async fn get_backend_status(state: State<'_, BackendState>) -> Result<BackendStatus, String> {
    let child_lock = state.child.lock().unwrap();
    let running = child_lock.is_some();
    Ok(BackendStatus {
        running,
        port: state.port,
        url: format!("http://localhost:{}", state.port),
    })
}

fn find_sidecar(resource_dir: &Path) -> Result<PathBuf, String> {
    // Try multiple possible locations
    let candidates = [
        resource_dir.join("backend/sidecar"),
        resource_dir.join("backend/sidecar.exe"),
        resource_dir.join("sidecar"),
        resource_dir.join("sidecar.exe"),
    ];

    for candidate in &candidates {
        if candidate.exists() {
            return Ok(candidate.clone());
        }
    }

    Err(format!("Sidecar not found in: {:?}", candidates))
}

fn get_data_dir() -> Result<PathBuf, String> {
    let base = dirs::data_dir()
        .or_else(|| dirs::home_dir())
        .ok_or("Could not find data directory")?;
    Ok(base.join("ai-video-clipper"))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_opener::init())
        .manage(BackendState {
            child: Mutex::new(None),
            port: 8000,
        })
        .invoke_handler(tauri::generate_handler![
            start_backend,
            stop_backend,
            get_backend_status
        ])
        .setup(|app| {
            // Auto-start backend on app launch
            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
                let _ = start_backend(app_handle, State::default()).await;
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}