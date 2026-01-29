            modal.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 100002;
                display: flex;
                align-items: flex-end;
                justify-content: center;
                pointer-events: none;
                animation: slideUp 0.4s ease;
            `;
            
            modal.innerHTML = `
                <style>
                    @keyframes slideUp { from { transform: translate(-50%, 50px); opacity: 0; } to { transform: translate(-50%, 0); opacity: 1; } }
                </style>
                <div style="
                    background: linear-gradient(145deg, #1e293b, #0f172a);
                    border-radius: 16px;
                    padding: 16px;
                    width: 280px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(99, 102, 241, 0.2);
                    position: relative;
                    overflow: hidden;
                    pointer-events: auto;
                ">
                    <!-- خلفية زخرفية -->
                    <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; opacity: 0.05; background-image: radial-gradient(#6366f1 1px, transparent 1px); background-size: 20px 20px; pointer-events: none;"></div>
                    
                    <!-- الأيقونة والعنوان -->
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <div style="
                            width: 36px;
                            height: 36px;
                            background: linear-gradient(135deg, #6366f1, #8b5cf6);
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 18px;
                            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
                        ">${icon}</div>
                        <div>
                            <h3 style="
                                color: white;
                                font-size: 15px;
                                font-weight: 700;
                                margin: 0;
                            ">${title}</h3>
                            <p style="color: #94a3b8; font-size: 11px; margin: 2px 0 0 0;">تابع الخطوات التالية للبدء</p>
                        </div>
                    </div>
                    
                    <!-- رسم توضيحي متحرك (منقط) -->
                    <div style="
                        background: rgba(99, 102, 241, 0.05);
                        border: 1px dashed rgba(99, 102, 241, 0.2);
                        border-radius: 8px;
                        padding: 8px;
                        text-align: center;
                        margin-bottom: 12px;
                        height: 50px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    ">
                        <svg width="150" height="40" viewBox="0 0 200 80" style="overflow: visible;">
                            <defs>
                                <linearGradient id="drawGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" style="stop-color:#6366f1;stop-opacity:1" />
                                    <stop offset="100%" style="stop-color:#ec4899;stop-opacity:1" />
                                </linearGradient>
                                <mask id="dashedMask">
                                    <path d="M30,60 Q70,0 120,20 T170,40" 
                                          fill="none" 
                                          stroke="white" 
                                          stroke-width="8" 
                                          stroke-dasharray="300"
                                          stroke-dashoffset="300">
                                        <animate attributeName="stroke-dashoffset" from="300" to="0" dur="2s" repeatCount="indefinite" />
                                    </path>
                                </mask>
                            </defs>
                            
                            <!-- دائرة البداية المجوفة -->
                            <circle cx="30" cy="60" r="5" fill="#1e293b" stroke="#6366f1" stroke-width="2" />
                            
                            <!-- الخط المنقط (يظهر باستخدام القناع) -->
                            <path d="M30,60 Q70,0 120,20 T170,40" 
                                fill="none" 
                                stroke="url(#drawGrad)" 
                                stroke-width="4" 
                                stroke-linecap="round" 
                                stroke-dasharray="8 8" 
                                mask="url(#dashedMask)"
                            />
                        </svg>
                    </div>
                    
                    <!-- الخطوات -->
                    <div style="background: rgba(0, 0, 0, 0.2); border-radius: 8px; padding: 10px; margin-bottom: 12px;">
                        ${steps.map((step, i) => `
                            <div style="
                                display: flex;
                                align-items: flex-start;
                                gap: 8px;
                                margin-bottom: ${i < steps.length - 1 ? '6px' : '0'};
                            ">
                                <span style="
                                    color: ${i === steps.length - 1 ? '#10b981' : '#cbd5e1'};
                                    font-size: 11px;
                                    line-height: 1.4;
                                    ${i === steps.length - 1 ? 'font-weight: 600;' : ''}
                                ">${step}</span>
                            </div>
                        `).join('')}
                    </div>
                    
                    <button onclick="closeSmartToolTutorial()" style="
                        width: 100%;
                        background: linear-gradient(135deg, #6366f1, #8b5cf6);
                        color: white;
                        border: none;
                        padding: 8px;
                        border-radius: 8px;
                        font-weight: 600;
                        font-size: 12px;
                        cursor: pointer;
                        box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
                        transition: all 0.2s;
                    " onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
                       فهمت، إغلاق
                    </button>
                    
                    <!-- زر إغلاق صغير في الزاوية -->
                    <button onclick="closeSmartToolTutorial()" style="
                        position: absolute;
                        top: 8px;
                        right: 8px;
                        background: transparent;
                        border: none;
                        color: #64748b;
                        cursor: pointer;
                        padding: 4px;
                        border-radius: 50%;
                        font-size: 14px;
                    " onmouseover="this.style.backgroundColor='rgba(255,255,255,0.1)';this.style.color='#ef4444'" onmouseout="this.style.backgroundColor='transparent';this.style.color='#64748b'">
                        ✕
                    </button>
                </div>
            `;
