#version 440
layout(location = 0) in vec4 qt_Vertex;
layout(location = 1) in vec2 qt_MultiTexCoord0;
layout(location = 0) out vec2 qt_TexCoord0;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec4 sourceRect;
    vec4 targetRect;
    float progress;
    float intensity;
    float edge;
};
void main() {
    qt_TexCoord0 = qt_MultiTexCoord0;
    vec2 uv = qt_MultiTexCoord0;
    bool vertical = edge < 1.5;
    float along = edge < 0.5 ? uv.y : edge < 1.5 ? 1.0-uv.y : edge < 2.5 ? uv.x : 1.0-uv.x;
    // The edge nearest the dock narrows first, then the far edge follows.
    float neck = smoothstep(0.0, 0.62, progress);
    float flow = smoothstep(0.30, 1.0, progress);
    float taper = mix(neck, flow, pow(1.0-along, max(0.2, intensity)));
    vec2 source = sourceRect.xy + uv * sourceRect.zw;
    vec2 target = targetRect.xy + uv * targetRect.zw;
    vec2 p = mix(source, target, vec2(vertical ? taper : flow, vertical ? flow : taper));
    gl_Position = qt_Matrix * vec4(p, 0.0, 1.0);
}
