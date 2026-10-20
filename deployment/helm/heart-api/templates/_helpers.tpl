{{/*
Common labels for heart-api Helm chart
*/}}
{{- define "heart-api.labels" -}}
app: {{ .Chart.Name }}
chart: {{ .Chart.Name }}-{{ .Chart.Version }}
release: {{ .Release.Name }}
{{- end }}
