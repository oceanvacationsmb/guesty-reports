}else{
  // PAYOUT: Accommodation = ACCOMMODATION FARE - MARKUP + LENGTH OF STAY DISCOUNT
  // Website fee = 1% of TOTAL PAYOUT (website only)
  // VRBO fee = 5% of TOTAL PAYOUT (VRBO only)
  html+="<tr><th>CODE</th><th>STAY</th><th>PLATFORM</th><th>ACCOMMODATION</th><th>WEBSITE/VRBO</th><th>PMC</th><th>OWNER PAYOUT</th></tr>";
  
  p.reservations.forEach(row=>{
    const totalPayout = num(row["TOTAL PAYOUT"]);
    const platform = (row["PLATFORM"] || "").toLowerCase();
    
    // Accommodation formula: FARE - MARKUP + DISCOUNT (NO community fee)
    let accom = num(row["ACCOMMODATION FARE"]) - num(row["MARKUP"]) + num(row["LENGTH OF STAY DISCOUNT"]);
    
    // Website/VRBO fee: 1% for website, 5% for VRBO, 0% for others
    let platformFee = 0;
    if(platform.includes("website") || platform.includes("manual")) {
      platformFee = totalPayout * 0.01; // 1%
    } else if(platform.includes("vrbo")) {
      platformFee = totalPayout * 0.05; // 5%
    }
    
    // PMC on the accommodation amount
    const pm = accom * t.percent;
    
    // Owner payout: accommodation - PMC - platform fee
    const ownerPayout = accom - pm - platformFee;
    
    const checkin = row["CHECK-IN DATE"] ? row["CHECK-IN DATE"].split("-").slice(1).join("/") : "";
    const checkout = row["CHECK-OUT DATE"] ? row["CHECK-OUT DATE"].split("-").slice(1).join("/") : "";
    
    if(totalPayout === 0) return;
    
    html += "<tr><td>" + (row["CONFIRMATION CODE"] || "").substring(0,8) + "</td><td>" + checkin + "-" + checkout + "</td><td>" + (row["PLATFORM"] || "") + "</td><td>" + money(accom) + "</td><td>" + money(platformFee) + "</td><td>" + money(pm) + "</td><td>" + money(ownerPayout) + "</td></tr>";
  });
  html+="</table></div>";
}
