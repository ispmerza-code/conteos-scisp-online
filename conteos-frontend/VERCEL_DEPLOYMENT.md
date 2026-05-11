# Vercel Deployment — Frontend Next.js (Conteos SCISP)

> **Tiempo estimado:** ~10 minutos

---

## Paso 1 — Importar el repositorio en Vercel

1. Ve a [vercel.com](https://vercel.com) e inicia sesion con GitHub (cuenta `ispmerza-code`)
2. Haz clic en **"Add New Project"**
3. Selecciona el repositorio **`conteos-scisp-online`**
4. En **"Root Directory"** haz clic en **Edit** y selecciona `conteos-frontend/`
   > Esto es clave porque el repo es monorepo (backend + frontend en una sola carpeta)
5. Vercel detectara automaticamente que es un proyecto Next.js
6. NO hagas Deploy todavia — primero configura las variables del Paso 2

---

## Paso 2 — Configurar variable de entorno

En la misma pantalla de configuracion, expande **"Environment Variables"** y agrega:

| Variable | Valor |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://tu-url.up.railway.app` |

> Reemplaza con la URL real que Railway te dio para el backend (sin `/` al final).
> La encuentras en Railway → servicio web → Settings → Domains.

---

## Paso 3 — Hacer Deploy

Haz clic en **"Deploy"**. Vercel instalara dependencias y construira el proyecto.

Cuando termine, obtendras una URL tipo:
`https://conteos-scisp-online.vercel.app`

---

## Paso 4 — Actualizar CORS en Railway

Una vez que tengas la URL de Vercel, actualiza la variable de entorno en Railway:

Railway → servicio web → Variables → `ALLOWED_ORIGINS`:
```
https://conteos-scisp-online.vercel.app
```

Esto permite que el frontend se comunique con el backend sin errores CORS.

---

## Paso 5 — Verificar

1. Visita tu URL de Vercel
2. Intenta iniciar sesion
3. Si funciona correctamente, el sistema esta desplegado en produccion

---

## Redeploy automatico

Cada `git push origin main` dispara un redeploy automatico en Vercel.

---

## Variables de entorno locales (desarrollo)

Crea un archivo `.env.local` en la carpeta `conteos-frontend/`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Este archivo ya esta en `.gitignore` y nunca se sube al repositorio.

---

## Troubleshooting

| Error | Solucion |
|-------|----------|
| Build falla con errores TS | `next.config.ts` ya tiene `ignoreBuildErrors: true` |
| CORS error en produccion | Verificar `ALLOWED_ORIGINS` en Railway con la URL exacta de Vercel |
| API no responde | Verificar que `NEXT_PUBLIC_API_URL` no tenga `/` al final |
| Root directory incorrecto | En Vercel → Settings → General → Root Directory → `conteos-frontend` |
