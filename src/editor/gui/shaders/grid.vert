#version 330

in vec2 position;

uniform mat4 matrix;

out vec2 world_position;

void main() {
    gl_Position = matrix * vec4(position, 0.0, 1.0);
    world_position = position;
}
