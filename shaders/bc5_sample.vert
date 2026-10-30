#version 450
layout(location = 0) out vec2 vUV;

void main() {
    vec2 positions[3] = vec2[](
        vec2(-1.0, -1.0),
        vec2( 3.0, -1.0),
        vec2(-1.0,  3.0)
    );
    vec2 p = positions[gl_VertexIndex];
    gl_Position = vec4(p, 0.0, 1.0);
    vec2 uv = p * 0.5 + 0.5;
    // Buffer row zero is the top row; flip V for a top-left image origin.
    vUV = vec2(uv.x, 1.0 - uv.y);
}
