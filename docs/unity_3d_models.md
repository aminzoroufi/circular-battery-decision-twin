# Unity 3D Model Sources

Downloaded source:

- Kenney Factory Kit 3.0
- Source page: https://kenney.nl/assets/factory-kit
- License: CC0 1.0 Universal
- Local license file: `unity/BatteryReXControlTwin/Assets/ThirdParty/KenneyFactoryKit/License.txt`

Unity import format used:

- FBX

Scene object mapping:

- Factory floor: `floor-large.fbx`
- Conveyor belt: `conveyor-long-stripe-sides.fbx`
- Inspection camera station: `scanner-high.fbx`
- AI decision station: `screen-panel-wide.fbx`
- Robot arm: generated `ABB CRB 15000 GoFa-style arm` from Unity primitives for animated pick/place.
- Lifecycle decision areas: `hopper-square.fbx` with neutral bin material plus colored Reuse / Remanufacture / Recycle / Quarantine plates.
- Runtime battery shapes: default unknown shape at intake, then generated cylindrical, pouch, or prismatic approximations after the AI response.
- Process pipe detail: `pipe-large-valve.fbx`
- Safety marker: `warning-traffic.fbx`
- Operator floor button: `button-floor-square.fbx`

If Unity opens the old primitive scene, use:

```text
Battery Re-X > Rebuild Demo Scene
```

If Unity is currently in Play mode, stop Play mode first so Unity can import script changes and rebuild the saved scene.
