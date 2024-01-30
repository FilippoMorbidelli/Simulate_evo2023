#version 330 core

out vec4 fragColor;

in vec4 clipCoords;

uniform samplerCube u_texture_cubemap_skybox;
uniform mat4 m_invProjView;
uniform vec3 SunPos;
uniform vec3 MoonPos;

vec3 SunCol = vec3 (255, 255, 37) / 255;
vec3 MoonCol = vec3 (255, 255, 118) / 255;

void main() {
    vec4 worldCoords = m_invProjView * clipCoords;
    vec3 texCubeCoord = normalize(worldCoords.xyz / worldCoords.w);

    float SunDist = (0.3 - length(texCubeCoord - SunPos))/0.3;
    float MoonDist = (0.15 - length(texCubeCoord - MoonPos))/0.15;

    //float SunExpDecay = (sqrt(3.0) + SunDist) / sqrt(3.0);

    if(SunDist < 0){SunDist = SunDist * 0.01;}
    if(MoonDist < 0){MoonDist = MoonDist * 0.01;}

    fragColor = texture(u_texture_cubemap_skybox, texCubeCoord);
    fragColor.rgb += SunCol * SunDist * 0.5;
    fragColor.rgb += MoonCol * MoonDist * 0.3;
}