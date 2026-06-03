# JVM Performance: AOT Class Loading (Java 24+)

AOT (Ahead-of-Time) features reduce startup time and time-to-peak-throughput without
modifying application code. Three JEPs form the complete picture:

| JEP | Java | Feature | Benefit |
|-----|------|---------|---------|
| 483 | 24 | AOT Class Loading & Linking | 42% faster startup (Spring PetClinic) |
| 514 | 25 | AOT Cache Ergonomics | Single-command workflow |
| 515 | 25 | AOT Method Profiling | 19% execution gain at startup |

---

## AOT Cache Workflow

### Single-command (Java 25+, JEP 514)

```bash
# Step 1: Build cache — training run, then cache creation in one command
java -XX:AOTCacheOutput=app.aot -cp app.jar com.example.Main

# Step 2: Run with the cache
java -XX:AOTCache=app.aot -cp app.jar com.example.Main
```

### Two-step workflow (Java 24, JEP 483)

```bash
# Record training data
java -XX:AOTMode=record \
     -XX:AOTConfiguration=app.aotconf \
     -cp app.jar com.example.Main

# Build cache from training data
java -XX:AOTMode=create \
     -XX:AOTConfiguration=app.aotconf \
     -XX:AOTCache=app.aot \
     -cp app.jar

# Run with cache
java -XX:AOTCache=app.aot -cp app.jar com.example.Main
```

### Spring Boot / Maven integration (Spring Boot 3.5+)

```xml
<plugin>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-maven-plugin</artifactId>
  <executions>
    <execution>
      <id>aot-cache</id>
      <goals><goal>aot-cache</goal></goals>
    </execution>
  </executions>
</plugin>
```

---

## Measured Startup Improvements

| Application | Without AOT | With AOT | Cache Size |
|---|---|---|---|
| HelloStream (minimal) | 0.031s | 0.018s (−42%) | 11.4 MB |
| Spring PetClinic (~21k classes) | 4.486s | 2.604s (−42%) | 130 MB |
| Typical microservice (~5k classes) | ~1.8s | ~1.0s (−44%) | ~40 MB |

---

## AOT Method Profiling (Java 25, JEP 515)

Pre-records JIT profiling data (method counts, branch frequencies, type profiles) from the
training run. On subsequent runs, the JIT generates optimized code from the first execution —
no warmup wait.

Method profiling is included automatically when using `-XX:AOTCacheOutput`.

```bash
# Verify profiling data was captured
java -XX:AOTCache=app.aot -Xlog:aot+class=info -cp app.jar com.example.Main
```

**Measured gain:** 19% execution improvement on Stream-heavy benchmarks (90ms → 73ms).
Cache overhead: ~250 KB.

---

## Container / Kubernetes Integration

```dockerfile
# Two-stage Dockerfile — build cache at image build time
FROM eclipse-temurin:25-jdk AS builder
WORKDIR /app
COPY target/app.jar .
RUN java -XX:AOTCacheOutput=app.aot -cp app.jar com.example.Main --aot-training-exit

FROM eclipse-temurin:25-jre AS runtime
WORKDIR /app
COPY --from=builder /app/app.jar .
COPY --from=builder /app/app.aot .
ENTRYPOINT ["java", "-XX:AOTCache=app.aot", "-cp", "app.jar", "com.example.Main"]
```

**Kubernetes benefit:** Faster startup → faster `readinessProbe` response → better HPA scaling.

---

## When to Use AOT

| Scenario | Recommended? | Notes |
|---|---|---|
| Kubernetes microservice | ✅ Yes | Faster HPA pod scaling |
| Serverless / FaaS | ✅ Yes | 42% cold start reduction, no code changes |
| Long-running batch job | ⚠️ Maybe | Startup gain is minor relative to total run time |
| Development workstation | ❌ No | Training run adds build time |
| CI integration tests | ✅ Yes | Speeds up slow test suite startup |

---

## Limitations

- Cache is **JDK-version-specific** — rebuild when upgrading JDK
- Cache is **classpath-specific** — rebuild when changing JARs
- Training run must exercise representative code paths — cold paths remain uninstrumented
- Native agents (`-javaagent`) may interfere with cache population

---

## Antipatterns

| Antipattern | Problem | Fix |
|---|---|---|
| Sharing AOT cache across JDK minor versions | Silent cache invalidation | Rebuild cache in CI on any JDK update |
| Using AOT cache without CI validation | Cache may be stale after dep update | Add cache rebuild as a CI step before container build |
| Training run that exits immediately | Empty cache — no classes pre-loaded | Training run must exercise main application paths |
