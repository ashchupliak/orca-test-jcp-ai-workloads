package com.jetbrains.orca.service;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/agent")
public class AgentController {

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of(
                "status", "healthy",
                "service", "agent",
                "port", 8001
        ));
    }

    @PostMapping("/execute")
    public ResponseEntity<Map<String, Object>> execute(@RequestBody(required = false) Map<String, Object> request) {
        String command = request != null && request.containsKey("command")
                ? request.get("command").toString()
                : "";

        Map<String, Object> response = new HashMap<>();
        response.put("service", "agent");
        response.put("command", command);

        try {
            // Check if Claude Code is available
            Process checkProcess = Runtime.getRuntime().exec(new String[]{"which", "claude-code"});
            BufferedReader reader = new BufferedReader(new InputStreamReader(checkProcess.getInputStream()));
            String claudePath = reader.readLine();
            checkProcess.waitFor();

            if (claudePath != null && !claudePath.isEmpty()) {
                response.put("result", "Claude Code is available at: " + claudePath);
                response.put("status", "ready");
                response.put("message", "Command would be executed: " + command);
            } else {
                response.put("result", "Claude Code not installed");
                response.put("status", "unavailable");
                response.put("message", "Install Claude Code to execute commands");
            }
        } catch (Exception e) {
            response.put("result", "Error checking Claude Code: " + e.getMessage());
            response.put("status", "error");
        }

        return ResponseEntity.ok(response);
    }

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> status() {
        Map<String, Object> response = new HashMap<>();
        response.put("service", "agent");

        try {
            Process process = Runtime.getRuntime().exec(new String[]{"which", "claude-code"});
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String claudePath = reader.readLine();
            process.waitFor();

            boolean available = claudePath != null && !claudePath.isEmpty();
            response.put("available", available);
            if (available) {
                response.put("claudePath", claudePath);
            }
        } catch (Exception e) {
            response.put("available", false);
            response.put("error", e.getMessage());
        }

        response.put("endpoints", Map.of(
                "health", "/agent/health",
                "execute", "/agent/execute",
                "status", "/agent/status"
        ));

        return ResponseEntity.ok(response);
    }
}
