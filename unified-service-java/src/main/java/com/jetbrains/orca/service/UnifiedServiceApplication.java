package com.jetbrains.orca.service;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@SpringBootApplication
public class UnifiedServiceApplication {

    public static void main(String[] args) {
        System.out.println("========================================");
        System.out.println("Unified Service Starting");
        System.out.println("========================================");
        System.out.println("Chat Service:  http://0.0.0.0:8000");
        System.out.println("Agent Service: http://0.0.0.0:8001");
        System.out.println("IDE Service:   http://0.0.0.0:8080");
        System.out.println("========================================");

        SpringApplication.run(UnifiedServiceApplication.class, args);
    }

    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurer() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins("*")
                        .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                        .allowedHeaders("*");
            }
        };
    }
}
