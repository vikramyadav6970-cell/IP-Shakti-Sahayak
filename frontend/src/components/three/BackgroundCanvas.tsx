import { Canvas } from '@react-three/fiber'
import { useReducedMotion } from 'framer-motion'
import { NebulaFog, ParticleField, StaticStarField } from './ParticleField'

/**
 * Full-screen 3D background canvas.
 * - frameloop="demand" for render-on-demand (coding_conventions.md rule 9)
 * - useReducedMotion() → static fallback (rule 7)
 */
export function BackgroundCanvas() {
  const prefersReducedMotion = useReducedMotion()

  return (
    <Canvas
      frameloop="demand"
      camera={{ position: [0, 0, 15], fov: 60 }}
      gl={{
        antialias: false,
        alpha: true,
        powerPreference: 'low-power',
      }}
      dpr={[1, 1.5]}
      style={{ background: 'transparent' }}
    >
      <color attach="background" args={['#030712']} />
      {prefersReducedMotion ? <StaticStarField /> : <ParticleField />}
      <NebulaFog />
    </Canvas>
  )
}
