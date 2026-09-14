export default function Sky() {
  return (
    <div className="sky" aria-hidden="true">
      <div className="horizon" />
      <div className="sun-bloom" />
      <div className="sun-core" />
      <div className="rays" />

      <div className="layer layer-far">
        <div className="cumulus c1"><i /><i /><i /><i /></div>
        <div className="cumulus c2"><i /><i /><i /></div>
      </div>
      <div className="layer layer-mid">
        <div className="cumulus c3"><i /><i /><i /><i /><i /></div>
        <div className="cumulus c4"><i /><i /><i /></div>
      </div>
      <div className="layer layer-near">
        <div className="cumulus c5"><i /><i /><i /><i /></div>
        <div className="cumulus c6"><i /><i /><i /></div>
      </div>
    </div>
  );
}
