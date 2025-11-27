package com.jetbrains.orca.service;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/ide")
public class IdeController {

    @GetMapping("/healthz")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of(
                "status", "healthy",
                "service", "ide",
                "port", 8080
        ));
    }

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> status() {
        Map<String, Object> response = new HashMap<>();
        response.put("service", "ide");

        try {
            // Check if code-server is available
            Process process = Runtime.getRuntime().exec(new String[]{"which", "code-server"});
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String codeServerPath = reader.readLine();
            process.waitFor();

            boolean available = codeServerPath != null && !codeServerPath.isEmpty();
            response.put("available", available);
            if (available) {
                response.put("codeServerPath", codeServerPath);
            }
        } catch (Exception e) {
            response.put("available", false);
            response.put("error", e.getMessage());
        }

        response.put("endpoints", Map.of(
                "health", "/ide/healthz",
                "status", "/ide/status"
        ));

        return ResponseEntity.ok(response);
    }
}
