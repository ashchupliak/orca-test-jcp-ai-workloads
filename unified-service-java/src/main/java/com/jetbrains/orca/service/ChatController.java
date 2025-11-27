package com.jetbrains.orca.service;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
public class ChatController {

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of(
                "status", "healthy",
                "service", "chat",
                "port", 8000
        ));
    }

    @PostMapping("/chat")
    public ResponseEntity<Map<String, Object>> chat(@RequestBody(required = false) Map<String, Object> request) {
        String message = request != null && request.containsKey("message")
                ? request.get("message").toString()
                : "";

        return ResponseEntity.ok(Map.of(
                "response", "Chat service received: " + message,
                "service", "chat",
                "status", "success"
        ));
    }

    @GetMapping("/chat/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of(
                "service", "chat",
                "available", true,
                "endpoints", Map.of(
                        "health", "/health",
                        "chat", "/chat",
                        "status", "/chat/status"
                )
        ));
    }
}
