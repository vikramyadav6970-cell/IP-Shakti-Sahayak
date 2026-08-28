import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import type { InstancedMesh } from 'three'
import * as THREE from 'three'

const PARTICLE_COUNT = 3500

/**
 * Animated particle field using instanced mesh for performance.
 * Particles drift with gentle sine wave motion.
 * Colors: teal (#2dd4bf) + violet (#8b5cf6) at low opacity.
 */
export function ParticleField() {
  const meshRef = useRef<InstancedMesh>(null)
  const dummy = useMemo(() => new THREE.Object3D(), [])

  // Pre-compute particle data
  const particles = useMemo(() => {
    const data: { x: number; y: number; z: number; speed: number; offset: number }[] = []
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      data.push({
        x: (Math.random() - 0.5) * 40,
        y: (Math.random() - 0.5) * 40,
        z: (Math.random() - 0.5) * 20 - 5,
        speed: 0.1 + Math.random() * 0.3,
        offset: Math.random() * Math.PI * 2,
      })
    }
    return data
  }, [])

  // Color array: mix of teal and violet
  const colors = useMemo(() => {
    const teal = new THREE.Color('#2dd4bf')
    const violet = new THREE.Color('#8b5cf6')
    const arr = new Float32Array(PARTICLE_COUNT * 3)
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const color = Math.random() > 0.5 ? teal : violet
      arr[i * 3] = color.r
      arr[i * 3 + 1] = color.g
      arr[i * 3 + 2] = color.b
    }
    return arr
  }, [])

  useFrame((state) => {
    if (!meshRef.current) return
    const time = state.clock.getElapsedTime()

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const p = particles[i]!
      dummy.position.set(
        p.x + Math.sin(time * p.speed + p.offset) * 0.5,
        p.y + Math.cos(time * p.speed * 0.7 + p.offset) * 0.3,
        p.z
      )
      dummy.scale.setScalar(0.015 + Math.sin(time * 0.5 + p.offset) * 0.005)
      dummy.updateMatrix()
      meshRef.current.setMatrixAt(i, dummy.matrix)
    }
    meshRef.current.instanceMatrix.needsUpdate = true

    // Invalidate for demand mode
    state.invalidate()
  })

  return (
    <instancedMesh ref={meshRef} args={[undefined, undefined, PARTICLE_COUNT]}>
      <sphereGeometry args={[1, 6, 6]} />
      <meshBasicMaterial transparent opacity={0.4}>
        <instancedBufferAttribute
          attach="geometry-attributes-color"
          args={[colors, 3]}
        />
      </meshBasicMaterial>
    </instancedMesh>
  )
}

/**
 * Static star field fallback for prefers-reduced-motion users.
 */
export function StaticStarField() {
  const positions = useMemo(() => {
    const arr = new Float32Array(PARTICLE_COUNT * 3)
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 40
      arr[i * 3 + 1] = (Math.random() - 0.5) * 40
      arr[i * 3 + 2] = (Math.random() - 0.5) * 20 - 5
    }
    return arr
  }, [])

  const colors = useMemo(() => {
    const teal = new THREE.Color('#2dd4bf')
    const violet = new THREE.Color('#8b5cf6')
    const arr = new Float32Array(PARTICLE_COUNT * 3)
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const color = Math.random() > 0.5 ? teal : violet
      arr[i * 3] = color.r
      arr[i * 3 + 1] = color.g
      arr[i * 3 + 2] = color.b
    }
    return arr
  }, [])

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
        <bufferAttribute
          attach="attributes-color"
          args={[colors, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        vertexColors
        transparent
        opacity={0.5}
        sizeAttenuation
      />
    </points>
  )
}

/**
 * Soft nebula fog effect — a large transparent plane with radial gradient.
 */
export function NebulaFog() {
  const texture = useMemo(() => {
    const size = 512
    const canvas = document.createElement('canvas')
    canvas.width = size
    canvas.height = size
    const ctx = canvas.getContext('2d')
    if (!ctx) return null

    const gradient = ctx.createRadialGradient(
      size / 2, size / 2, 0,
      size / 2, size / 2, size / 2
    )
    gradient.addColorStop(0, 'rgba(45, 212, 191, 0.08)')
    gradient.addColorStop(0.4, 'rgba(139, 92, 246, 0.04)')
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)')

    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, size, size)

    const tex = new THREE.CanvasTexture(canvas)
    return tex
  }, [])

  if (!texture) return null

  return (
    <mesh position={[0, 0, -10]}>
      <planeGeometry args={[50, 50]} />
      <meshBasicMaterial map={texture} transparent depthWrite={false} />
    </mesh>
  )
}
