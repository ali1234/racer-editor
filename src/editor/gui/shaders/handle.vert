#version 330

in vec4 position;
in float distance;
in int selected;

uniform vec4 unselected_colour;
uniform vec4 selected_colour;

uniform mat4 matrix;
uniform int mode;

out vec4 colour;

void main(void)
{
   if (mode == 4) {
      gl_Position = matrix * vec4(distance, position.z, 0, 1);
   } else {
      gl_Position = matrix * position;
   }
   colour = (selected == 1) ? selected_colour : unselected_colour;
}
